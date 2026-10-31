// Shown while a page loads its data from the Django API
export default function Loading() {
  return <section style={{ minHeight: "70vh" }} aria-busy="true"></section>;
}
