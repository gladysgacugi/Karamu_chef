// One chef application: documents, dish photos, details, and approve or reject (Django: team/application.html).
import type { Metadata } from "next";
import Link from "next/link";
import ActionForm from "@/components/ActionForm";
import { Widget } from "@/components/DjangoForm";
import { getTeamPage, type ApplicationDetail, type Field } from "@/lib/api";
import { chefUrl, dayMonthYear, pluralize, waLink } from "@/lib/format";

type ApplicationPage = { application: ApplicationDetail; approve_fields: Field[]; reject_fields: Field[] };

const getApplicationPage = (id: string) => getTeamPage<ApplicationPage>(`applications/${encodeURIComponent(id)}/`);

export async function generateMetadata({ params }: PageProps<"/team/applications/[id]">): Promise<Metadata> {
  return { title: (await getApplicationPage((await params).id)).application.full_name };
}

/** A textarea with its label and help text, as the template renders {{ form.message }} */
function TextField({ field }: { field: Field }) {
  return (
    <>
      <label className="flbl" htmlFor={`id_${field.name}`}>{field.label}</label>
      <Widget field={field} invalid={false} />
      <p className="tmnote mt-1">{field.help_text}</p>
    </>
  );
}

export default async function ApplicationPage({ params }: PageProps<"/team/applications/[id]">) {
  const { application: app, approve_fields, reject_fields } = await getApplicationPage((await params).id);
  const chef = app.chef;

  return (
    <>
      <Link href="/team/applications/" className="dbback"><i className="fas fa-arrow-left me-1"></i>Applications</Link>
      <h1 className="tmtitle">{app.full_name}<small>Applied {dayMonthYear(app.created_at)} &middot; {app.status_display}</small></h1>

      <div className="tmrow mt-0 mb-3">
        <a className="bkbtn bkbtn-wa" href={waLink(app.phone, `Hi ${app.full_name}, this is Karamu about your chef application.`)} target="_blank" rel="noopener"><i className="fab fa-whatsapp"></i>WhatsApp</a>
        <a className="bkbtn bkbtn-plain" href={`tel:${app.phone}`}><i className="fas fa-phone-alt"></i>Call</a>
        <a className="bkbtn bkbtn-plain" href={`mailto:${app.email}`}><i className="fas fa-envelope"></i>Email</a>
      </div>

      <div className="tmcard">
        <h2 className="tmsub mb-0">Documents</h2>
        <p className="tmnote mt-1 mb-2">Tap to open. Check the ID name matches the application.</p>
        <div className="tmdocs">
          <a href={app.national_id} target="_blank" rel="noopener"><i className="fas fa-id-card"></i>National ID</a>
          <a href={app.food_handler_certificate} target="_blank" rel="noopener"><i className="fas fa-certificate"></i>Food handler&apos;s cert</a>
        </div>
      </div>

      {app.dish_photos.length > 0 && (
        <div className="tmcard">
          <h2 className="tmsub">Dish photos</h2>
          <div className="tmphotos">
            {app.dish_photos.map((url, i) => <a key={url} href={url} target="_blank" rel="noopener"><img src={url} alt={`Dish photo ${i + 1}`} /></a>)}
          </div>
        </div>
      )}

      <div className="tmcard">
        <h2 className="tmsub mb-0">Details</h2>
        <dl className="tmdl">
          <dt>Phone (M-Pesa)</dt><dd>{app.phone}</dd>
          <dt>Email</dt><dd>{app.email}</dd>
          <dt>Location</dt><dd>{app.location}</dd>
          <dt>Type</dt><dd>{app.chef_type_display}, {app.years_experience} year{pluralize(app.years_experience)} experience</dd>
          <dt>Services</dt><dd>{app.services_display}</dd>
          <dt>Main cuisine</dt><dd>{app.cuisine_display}</dd>
          <dt>About them</dt><dd>{app.bio}</dd>
          {app.admin_notes && <><dt>Team notes</dt><dd>{app.admin_notes}</dd></>}
          {app.decision_message && <><dt>{app.status === "rejected" ? "Reason we gave" : "Welcome message sent"}</dt><dd>{app.decision_message}</dd></>}
        </dl>
      </div>

      {chef ? (
        <div className="tmcard">
          <div className="bktop">
            <span className="bkname">{chef.name}</span>
            <span className={`bkstatus ${chef.is_active ? "bk-confirmed" : "bk-new"}`}>{chef.is_active ? "Live" : "Not live yet"}</span>
          </div>
          <p className="tmnote mt-0">
            {chef.has_login ? `Login sent to ${chef.email}.` : "No login yet."}
            {!chef.is_active && " Check they have added a photo, packages and prices before putting the profile live."}
          </p>
          <div className="tmrow">
            <a className="bkbtn bkbtn-plain" href={chefUrl(chef.slug)} target="_blank" rel="noopener"><i className="fas fa-eye"></i>View profile</a>
            <ActionForm action={`/api/team/chefs/${chef.id}/live/`} confirm={chef.is_active ? `Hide ${chef.name} from the marketplace?` : undefined}>
              <input type="hidden" name="on" value={chef.is_active ? "0" : "1"} />
              {chef.is_active
                ? <button type="submit" className="bkbtn bkbtn-ghost"><i className="fas fa-eye-slash"></i>Hide</button>
                : <button type="submit" className="bkbtn"><i className="fas fa-rocket"></i>Put live</button>}
            </ActionForm>
          </div>
        </div>
      ) : (
        <div className="tmcard">
          <h2 className="tmsub">Decision</h2>
          <ActionForm action={`/api/team/applications/${app.id}/approve/`} confirm={`Approve ${app.full_name}? They will get a welcome email with their login.`}>
            {approve_fields.map((field) => <TextField key={field.name} field={field} />)}
            <div className="tmrow"><button type="submit" className="bkbtn bkbtn-big"><i className="fas fa-check"></i>Approve &amp; send login</button></div>
          </ActionForm>
          <p className="tmnote">Approving creates their chef profile (hidden until you put it live) and emails them a link to set their password.</p>
          {app.status !== "rejected" && (
            <details className="mt-3">
              <summary>Reject this application</summary>
              <ActionForm action={`/api/team/applications/${app.id}/reject/`} confirm={`Reject ${app.full_name}? They will be emailed.`}>
                {reject_fields.map((field) => <TextField key={field.name} field={field} />)}
                <div className="tmrow"><button type="submit" className="bkbtn bkbtn-ghost"><i className="fas fa-times"></i>Reject &amp; email them</button></div>
              </ActionForm>
            </details>
          )}
        </div>
      )}
    </>
  );
}
