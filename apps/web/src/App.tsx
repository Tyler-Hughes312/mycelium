import { useRef } from "react";
import { useScrollTheater } from "./hooks/useScrollTheater";
import { SiteNav } from "./components/SiteNav";
import { Hero } from "./components/Hero";
import { Outcomes } from "./components/Outcomes";
import { Capabilities } from "./components/Capabilities";
import { Setup } from "./components/Setup";
import { Impact } from "./components/Impact";
import { SiteFooter } from "./components/SiteFooter";

export default function App() {
  const rootRef = useRef<HTMLDivElement>(null);
  useScrollTheater(rootRef);

  return (
    <div ref={rootRef}>
      <SiteNav />
      <main>
        <Hero />
        <Capabilities />
        <div className="page-ribbon">
          <Outcomes />
          <Setup />
          <Impact />
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
