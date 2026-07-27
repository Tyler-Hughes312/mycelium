import { useEffect, type RefObject } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { getPrefersReducedMotion } from "./prefersReducedMotion";

gsap.registerPlugin(ScrollTrigger);
ScrollTrigger.config({ ignoreMobileResize: true });

export function useScrollTheater(rootRef: RefObject<HTMLElement | null>): void {
  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    if (getPrefersReducedMotion()) {
      root.dataset.motion = "reduced";
      return;
    }

    root.dataset.motion = "full";
    // Same smooth-scroll + pin theater on phone and desktop.
    const lenis = new Lenis({
      autoRaf: true,
      syncTouch: true,
      touchMultiplier: 1.1,
    });
    lenis.on("scroll", ScrollTrigger.update);

    const ctx = gsap.context(() => {
      const hyphaPaths = root.querySelectorAll<SVGPathElement>("[data-hypha-path]");
      if (hyphaPaths.length > 0) {
        hyphaPaths.forEach((path) => {
          const length =
            Number(path.getAttribute("stroke-dasharray")) || path.getTotalLength();
          gsap.set(path, { strokeDashoffset: length });
        });
        gsap.to(hyphaPaths, {
          strokeDashoffset: 0,
          duration: 1.4,
          stagger: 0.06,
          ease: "power2.out",
        });
      }

      const heroAnimate = root.querySelectorAll("[data-hero-animate]");
      if (heroAnimate.length > 0) {
        gsap.from(heroAnimate, {
          opacity: 0,
          y: 32,
          duration: 1,
          stagger: 0.12,
          ease: "power2.out",
        });
      }

      // ≤2 pins: capabilities horizontal scrub + setup steps (all viewports).
      const capabilities = root.querySelector<HTMLElement>(
        "[data-chapter='capabilities']",
      );
      const capsTrack = root.querySelector<HTMLElement>("[data-caps-track]");
      if (capabilities && capsTrack) {
        const total = capsTrack.scrollWidth - capabilities.clientWidth;
        gsap.to(capsTrack, {
          x: () => -Math.max(total, 0),
          ease: "none",
          scrollTrigger: {
            trigger: capabilities,
            start: "top top",
            end: () => `+=${Math.max(total, capabilities.clientHeight)}`,
            pin: true,
            scrub: 1,
            anticipatePin: 1,
            invalidateOnRefresh: true,
          },
        });
      }

      const setup = root.querySelector<HTMLElement>("[data-chapter='setup']");
      if (setup) {
        const steps = setup.querySelectorAll("[data-setup-step]");
        if (steps.length > 0) {
          gsap
            .timeline({
              scrollTrigger: {
                trigger: setup,
                start: "top top",
                end: "+=120%",
                pin: true,
                scrub: 1,
                anticipatePin: 1,
              },
            })
            .from(steps, { opacity: 0.15, y: 40, stagger: 0.2 });
        }
      }
    }, root);

    const onLoad = () => ScrollTrigger.refresh();
    const onResize = () => ScrollTrigger.refresh();
    window.addEventListener("load", onLoad);
    window.addEventListener("orientationchange", onResize);

    return () => {
      window.removeEventListener("load", onLoad);
      window.removeEventListener("orientationchange", onResize);
      ctx.revert();
      lenis.destroy();
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    };
  }, [rootRef]);
}
