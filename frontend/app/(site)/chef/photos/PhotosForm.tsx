"use client";

// Add several food photos at once, change captions, remove (Django: chef/photos.html).
import { FieldErrors, useDjangoForm, Widget } from "@/components/DjangoForm";
import type { Field, Formset } from "@/lib/api";

export default function PhotosForm({ add, photos, images, maxPhotos }: { add: Field[]; photos: Formset; images: string[]; maxPhotos: number }) {
  const { errors, sending, formRef, onSubmit } = useDjangoForm("/api/chef/photos/");
  const newPhotos = add[0];

  return (
    <form ref={formRef} onSubmit={onSubmit} noValidate tabIndex={-1}>
      {Object.keys(errors).length > 0 && <div className="acmsg acmsg-err"><i className="fas fa-exclamation-circle"></i>Please correct the highlighted fields.</div>}
      <div className="fcard dbcard">
        <h4>Add photos</h4>
        <p className="acsub">You have {photos.forms.length} of {maxPhotos}. You can pick several photos at once.</p>
        <label className="flbl" htmlFor={`id_${newPhotos.name}`}>{newPhotos.label}</label>
        <Widget field={newPhotos} invalid={!!errors[newPhotos.name]} />
        <small style={{ color: "#999", fontSize: ".75rem" }}>{newPhotos.help_text}</small>
        <FieldErrors errors={errors} name={newPhotos.name} />
      </div>

      <div className="fcard dbcard mt-4">
        <h4>Your photos</h4>
        {photos.management.map((field) => <Widget key={field.name} field={field} invalid={false} />)}
        <FieldErrors errors={errors} name="__all__" />
        <div className="dbgallery">
          {photos.forms.map((form, i) => {
            const field = (name: string) => form.find((f) => f.name.endsWith(`-${name}`))!;
            const caption = field("caption");
            return (
              <div key={caption.name} className="dbshot">
                {form.filter((f) => f.type === "hidden").map((f) => <Widget key={f.name} field={f} invalid={false} />)}
                <img src={images[i]} alt={String(caption.value)} />
                <Widget field={caption} invalid={!!errors[caption.name]} />
                <FieldErrors errors={errors} name={caption.name} />
                <label className="dbdel"><Widget field={field("DELETE")} invalid={false} /> Remove</label>
              </div>
            );
          })}
          {photos.forms.length === 0 && <p className="acsub mb-0">No photos yet. Add a few above so customers can see your food.</p>}
        </div>
      </div>
      <div className="dbsave">
        <button type="submit" className="btn-red" disabled={sending}><i className={`fas ${sending ? "fa-spinner fa-spin" : "fa-save"}`}></i>Save photos</button>
      </div>
    </form>
  );
}
