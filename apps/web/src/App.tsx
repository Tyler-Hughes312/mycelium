import { useRef } from "react";
import { useScrollTheater } from "./hooks/useScrollTheater";
import { SiteNav } from "./components/SiteNav";
import { Hero } from "./components/Hero";
import { Capabilities } from "./components/Capabilities";
import { Setup } from "./components/Setup";
import { GetIt } from "./components/GetIt";
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
        <Setup />
        <GetIt />
      </main>
      <SiteFooter />
    </div>
  );
}
