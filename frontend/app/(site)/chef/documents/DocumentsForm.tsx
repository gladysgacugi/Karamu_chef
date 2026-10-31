"use client";

// Upload a new ID or food handler's certificate (Django: chef/documents.html).
import { FieldErrors, useDjangoForm, Widget } from "@/components/DjangoForm";
import type { Field } from "@/lib/api";

export default function DocumentsForm({ fields, verified }: { fields: Field[]; verified: boolean }) {
  const { errors, sending, formRef, onSubmit } = useDjangoForm("/api/chef/documents/");

  return (
    <form ref={formRef} onSubmit={onSubmit} noValidate tabIndex={-1}>
      {(errors.__all__ ?? []).map((error) => <p key={error} className="ferr mb-2"><i className="fas fa-exclamation-circle me-1"></i>{error}</p>)}
      {fields.map((field) => (
        <div key={field.name} className="dbitem">
          <label className="flbl" htmlFor={`id_${field.name}`}>{field.label}</label>
          {field.url ? (
            <p className="dbfile"><i className="fas fa-file-alt"></i><a href={field.url} target="_blank" rel="noopener">View current file</a></p>
          ) : (
            <p className="dbfile"><i className="fas fa-exclamation-circle"></i>Not uploaded yet</p>
          )}
          <Widget field={{ ...field, url: "" }} invalid={!!errors[field.name]} />
          <small className="achelp">PDF, JPG or PNG, up to 5 MB.{field.url && " Leave empty to keep the current file."}</small>
          <FieldErrors errors={errors} name={field.name} />
        </div>
      ))}
      {verified && <p className="paynote"><i className="fas fa-info-circle"></i>Your &quot;verified&quot; badge is hidden while we check a new upload.</p>}
      <button type="submit" className="btn-red mt-3" disabled={sending}><i className={`fas ${sending ? "fa-spinner fa-spin" : "fa-upload"}`}></i>Upload</button>
    </form>
  );
}
