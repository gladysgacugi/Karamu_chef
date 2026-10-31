// The chef application form, on the homepage and the Become a Chef page (Django: partials/chef_application_form.html).
// Once sent, it goes to the Become a Chef page's thank-you, like the Django form.
import DjangoForm from "@/components/DjangoForm";
import type { Field } from "@/lib/api";

export default function ChefApplicationForm({ fields, idPrefix }: { fields: Field[]; idPrefix?: string }) {
  return (
    <DjangoForm
      action="/api/chef-applications/"
      fields={fields}
      idPrefix={idPrefix}
      wide={["bio", "dish_photos"]}
      showHelp
      checkboxNote={<a href="/terms/" target="_blank" style={{ color: "var(--primary)" }}>Read the terms</a>}
      errorBanner="Please correct the highlighted fields below."
      icon="fa-user-plus"
      button="Submit Application"
    />
  );
}
