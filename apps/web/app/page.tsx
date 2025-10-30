import { Navbar, Hero, FeatureGrid, HowItWorks, Samples, CodeTabs, Footer } from "@ui";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <FeatureGrid />
        <HowItWorks />
        <Samples />
        <CodeTabs />
      </main>
      <Footer />
    </>
  );
}
