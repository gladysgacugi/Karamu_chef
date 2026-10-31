// The card the login, sign-up and password pages sit in (Django: accounts/auth_base.html).
export default function AuthCard({ eyebrow = "Karamu", heading, children }: {
  eyebrow?: string;
  heading: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="acwrap">
      <div className="container">
        <div className="accard fcard">
          <span className="slbl">{eyebrow}</span>
          <h1 className="actitle">{heading}</h1>
          {children}
        </div>
      </div>
    </section>
  );
}
