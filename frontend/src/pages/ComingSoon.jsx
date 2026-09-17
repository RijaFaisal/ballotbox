import SiteHeader from "../components/SiteHeader.jsx";

export default function ComingSoon() {
  return (
    <div className="site-shell">
      <SiteHeader />
      <main className="site-main">
        <div className="panel panel--raised">
          <span className="eyebrow">BallotBox</span>
          <h1>Entries open soon</h1>
          <p>This ballot isn't accepting entries yet. Check back shortly.</p>
        </div>
      </main>
    </div>
  );
}
