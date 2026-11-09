/** "Do a barrel roll": spins the whole app (#root) once, unless motion is reduced. */

import { motionReduced } from "../store";

let rolling = false;

export function barrelRoll(): void {
  if (rolling || motionReduced()) return;
  const root = document.getElementById("root");
  if (!root || typeof root.animate !== "function") return;
  rolling = true;
  const anim = root.animate([{ transform: "rotate(0deg)" }, { transform: "rotate(360deg)" }], {
    duration: 1000,
    easing: "cubic-bezier(0.45, 0.05, 0.35, 1)",
  });
  const done = () => {
    rolling = false;
  };
  anim.onfinish = done;
  anim.oncancel = done;
}
