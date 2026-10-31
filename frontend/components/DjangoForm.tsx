"use client";

// A Django form, rendered from its description (lib/api.ts Field) the way the templates render {% for field in form %},
// and sent to the API from the browser. Validation happens in Django; its errors show under each field.
import { useRef, useState, type ReactNode } from "react";
import type { Field } from "@/lib/api";
import { goTo, post, type Answer, type Errors } from "@/lib/client";

// Django widget attributes that React spells differently
const REACT_ATTRS: Record<string, string> = {
  class: "className", autocomplete: "autoComplete", autocapitalize: "autoCapitalize", autofocus: "autoFocus",
  maxlength: "maxLength", minlength: "minLength", readonly: "readOnly",
};

const reactAttrs = (attrs: Field["attrs"]) =>
  Object.fromEntries(Object.entries(attrs).map(([key, value]) => [REACT_ATTRS[key] ?? key, value]));

/** {{ field }}. Uncontrolled unless `controlled` is given, so the browser keeps what was typed. */
export function Widget({ field, invalid, controlled, idPrefix = "id_" }: {
  field: Field;
  invalid: boolean;
  controlled?: { value: string; onChange: (value: string) => void };
  idPrefix?: string;
}) {
  const id = `${idPrefix}${field.name}`;
  const common = { name: field.name, id, "aria-invalid": invalid || undefined, ...reactAttrs(field.attrs) };
  const value = controlled
    ? { value: controlled.value, onChange: (e: { target: { value: string } }) => controlled.onChange(e.target.value) }
    : { defaultValue: String(field.value) };

  if (field.type === "textarea") return <textarea {...common} {...value} />;
  if (field.type === "select") {
    return (
      <select {...common} {...value}>
        {field.choices.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
      </select>
    );
  }
  if (field.type === "checkbox") return <input type="checkbox" {...common} defaultChecked={field.value === true} />;
  if (field.type === "checkboxes") {
    // CheckboxSelectMultiple
    const checked = Array.isArray(field.value) ? field.value : [];
    return (
      <div id={id}>
        {field.choices.map(([v, label], i) => (
          <div key={v}>
            <label htmlFor={`${id}_${i}`}>
              <input type="checkbox" name={field.name} value={v} id={`${id}_${i}`} defaultChecked={checked.includes(v)} /> {label}
            </label>
          </div>
        ))}
      </div>
    );
  }
  if (field.type === "file") {
    // ClearableFileInput's "Currently: ... Clear" when a file is already saved
    return (
      <>
        {field.url && (
          <p className="dbfile">
            <i className="fas fa-file-alt"></i><a href={field.url} target="_blank" rel="noopener">View current file</a>
            {field.clearable && <label className="dbdel ms-3"><input type="checkbox" name={`${field.name}-clear`} />Remove it</label>}
          </p>
        )}
        <input type="file" {...common} />
      </>
    );
  }
  if (field.type === "password") return <input type="password" {...common} />;
  return <input type={field.type} {...common} {...value} />;
}

/** A field's errors, under it. */
export function FieldErrors({ errors, name }: { errors: Errors; name: string }) {
  return (errors[name] ?? []).map((error) => <small key={error} className="ferr">{error}</small>);
}

/**
 * Sends a form to the API from the browser and keeps its errors. When it was saved: `onDone`, or by default go to the
 * answer's redirect, or show its message (`message`) and clear the form.
 */
export function useDjangoForm(action: string, onDone?: (answer: Answer) => void) {
  const [errors, setErrors] = useState<Errors>({});
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    setSending(true);
    setMessage("");
    const answer = await post(action, new FormData(form));
    setSending(false);
    setErrors(answer.errors ?? {});

    if (answer.errors) {
      const first = Object.keys(answer.errors).find((name) => name !== "__all__");
      (first ? form.querySelector<HTMLElement>(`[name="${first}"]`) : formRef.current)?.focus?.();
      if (!first) formRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (onDone) {
      onDone(answer);
    } else if (answer.redirect) {
      goTo(answer.redirect, answer.message, false, answer.warning);
    } else {
      form.reset(); // like the page reload after a Django form
      setMessage(answer.message ?? "");
    }
  }

  return { errors, message, sending, formRef, onSubmit };
}

export type DjangoFormProps = {
  /** The API endpoint, e.g. "/api/contact/" */
  action: string;
  fields: Field[];
  /** "columns": two per row like the homepage and booking forms. "stacked": one per row like the account pages. */
  variant?: "columns" | "stacked";
  /** Fields that take the whole row in "columns" */
  wide?: string[];
  /** Mark required fields with * ("columns" only) */
  stars?: boolean;
  /** Show each field's help text */
  showHelp?: boolean;
  /** Help text of our own for some fields, shown while the field has no error */
  helpFor?: Record<string, string>;
  /** Shown after a checkbox's label, e.g. a link to the terms */
  checkboxNote?: ReactNode;
  hidden?: Record<string, string>;
  /** Shown between the fields and the button */
  extra?: ReactNode;
  icon: string;
  button: string;
  buttonClass?: string;
  /** Text for the banner shown when fields have errors */
  errorBanner?: string;
  controlled?: Record<string, { value: string; onChange: (value: string) => void }>;
  /** Starts each field's id, for pages with several forms (Django uses "id_" for all of them) */
  idPrefix?: string;
  /** What to do when the form was saved. By default: go to the answer's redirect, or show its message here. */
  onDone?: (answer: Answer) => void;
};

export default function DjangoForm({
  action, fields, variant = "columns", wide = [], stars = variant === "columns", showHelp = variant === "stacked",
  helpFor = {}, checkboxNote, hidden = {}, extra, icon, button, buttonClass, errorBanner = "Please correct the highlighted fields.",
  controlled = {}, idPrefix = "id_", onDone,
}: DjangoFormProps) {
  const { errors, message, sending, formRef, onSubmit } = useDjangoForm(action, onDone);

  const nonField = errors.__all__ ?? [];
  const hasErrors = Object.keys(errors).length > 0;
  const stacked = variant === "stacked";

  const fieldList = fields.map((field) => {
    if (field.type === "hidden") return <Widget key={field.name} field={field} invalid={false} idPrefix={idPrefix} />;
    const fieldErrors = errors[field.name] ?? [];
    const errorList = <FieldErrors errors={errors} name={field.name} />;
    const widget = <Widget field={field} invalid={fieldErrors.length > 0} controlled={controlled[field.name]} idPrefix={idPrefix} />;

    if (field.type === "checkbox") {
      return (
        <div key={field.name} className="col-12">
          <label style={{ fontSize: ".85rem", color: "#555", display: "flex", gap: 9, alignItems: "flex-start" }}>
            {widget} <span>{field.label} {checkboxNote}</span>
          </label>
          {errorList}
        </div>
      );
    }

    const help = helpFor[field.name] ?? (showHelp ? field.help_text : "");
    return (
      <div key={field.name} className={stacked || wide.includes(field.name) ? "col-12" : "col-sm-6"}>
        <label className="flbl" htmlFor={`${idPrefix}${field.name}`}>{field.label}{stars && field.required && " *"}</label>
        {widget}
        {help && fieldErrors.length === 0 && (stacked
          // Django's password help is HTML (a list of the rules)
          ? <small className="achelp" dangerouslySetInnerHTML={{ __html: help }} />
          : <small className="achelp">{help}</small>)}
        {errorList}
      </div>
    );
  });

  const submit = (
    <button type="submit" className={buttonClass ?? "btn-red w-100 justify-content-center"} disabled={sending}>
      <i className={`fas ${sending ? "fa-spinner fa-spin" : icon}`}></i>{button}
    </button>
  );

  return (
    <>
      {message && <div className="sucmsg" style={{ display: "block", margin: "0 0 20px" }}><i className="fas fa-check-circle"></i><p>{message}</p></div>}
      {nonField.map((error) => <p key={error} className="ferr mb-2"><i className="fas fa-exclamation-circle me-1"></i>{error}</p>)}
      {!stacked && hasErrors && nonField.length === 0 && <p className="ferr mb-2"><i className="fas fa-exclamation-circle me-1"></i>{errorBanner}</p>}
      <form ref={formRef} onSubmit={onSubmit} noValidate tabIndex={-1}>
        {Object.entries(hidden).map(([name, value]) => <input key={name} type="hidden" name={name} value={value} />)}
        <div className="row g-3">
          {fieldList}
          {!stacked && <div className="col-12">{extra}{submit}</div>}
        </div>
        {stacked && <>{extra}{submit}</>}
      </form>
    </>
  );
}
