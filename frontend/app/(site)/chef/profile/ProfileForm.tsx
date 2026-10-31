"use client";

// The profile and the packages formset, saved together (Django: chef/profile_edit.html).
import Link from "next/link";
import { FieldErrors, useDjangoForm, Widget } from "@/components/DjangoForm";
import type { Field, Formset } from "@/lib/api";
import type { Errors } from "@/lib/client";

const WIDE = ["headline", "bio", "services"];

/** A field's name without the formset prefix: "packages-0-price" is "price". */
const baseName = (field: Field) => field.name.split("-").pop()!;

function PackageFields({ fields, errors }: { fields: Field[]; errors: Errors }) {
  const saved = fields.some((field) => baseName(field) === "id" && field.value);
  return (
    <div className="dbitem">
      {fields.filter((field) => field.type === "hidden").map((field) => <Widget key={field.name} field={field} invalid={false} />)}
      <div className="row g-2">
        {fields.filter((field) => field.type !== "hidden").map((field) => {
          const name = baseName(field);
          const widget = <Widget field={field} invalid={!!errors[field.name]} />;
          if (name === "DELETE") {
            return saved ? <div key={field.name} className="col-12"><label className="dbdel">{widget} Remove this package</label></div> : null;
          }
          if (name === "is_active") {
            return <div key={field.name} className="col-12"><label className="dbdel">{widget} {field.label} <small>(untick to hide it for now)</small></label></div>;
          }
          return (
            <div key={field.name} className={name === "name" || name === "description" ? "col-12" : "col-sm-4"}>
              <label className="flbl" htmlFor={`id_${field.name}`}>{field.label}</label>
              {widget}
              <FieldErrors errors={errors} name={field.name} />
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ProfileForm({ fields, packages }: { fields: Field[]; packages: Formset }) {
  const { errors, sending, formRef, onSubmit } = useDjangoForm("/api/chef/profile/");

  return (
    <form ref={formRef} onSubmit={onSubmit} noValidate tabIndex={-1}>
      {Object.keys(errors).length > 0 && <div className="acmsg acmsg-err"><i className="fas fa-exclamation-circle"></i>Please correct the highlighted fields.</div>}
      <div className="row g-4">
        <div className="col-lg-7">
          <div className="fcard dbcard">
            <h4>Profile</h4>
            <div className="row g-3">
              {fields.map((field) => {
                const widget = <Widget field={field} invalid={!!errors[field.name]} />;
                return (
                  <div key={field.name} className={WIDE.includes(field.name) ? "col-12" : "col-sm-6"}>
                    <label className="flbl" htmlFor={`id_${field.name}`}>{field.label}</label>
                    {field.type === "checkboxes" ? <div className="dbchecks">{widget}</div> : widget}
                    {field.help_text && !errors[field.name] && <small className="achelp">{field.help_text}</small>}
                    <FieldErrors errors={errors} name={field.name} />
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="col-lg-5">
          <div className="fcard dbcard">
            <h4>Packages &amp; prices</h4>
            <p className="acsub">The offers customers can pick when booking, and what each costs. Fill in the blank one to add a package; save and another blank one appears. Days off and pausing bookings are on the <Link href="/chef/availability/">Availability</Link> page.</p>
            {packages.management.map((field) => <Widget key={field.name} field={field} invalid={false} />)}
            <FieldErrors errors={errors} name="__all__" />
            {packages.forms.map((form) => <PackageFields key={form[0].name} fields={form} errors={errors} />)}
          </div>

          <p className="acsub mt-3"><i className="fas fa-images me-1"></i>Food photos are on their own page: <Link href="/chef/photos/">add or change photos</Link>.</p>
        </div>
      </div>
      <div className="dbsave">
        <button type="submit" className="btn-red" disabled={sending}><i className={`fas ${sending ? "fa-spinner fa-spin" : "fa-save"}`}></i>Save changes</button>
      </div>
    </form>
  );
}
