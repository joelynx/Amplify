/**
 * The easter-egg catalogue (Makeover.md §6) shown in the Collection log.
 * Each id is the secret recorded in the store (configs.EASTER_EGGS) when the
 * egg is found. Hints stay vague on purpose; rewards are titles, except
 * Vaporwave, which unlocks the hidden preset.
 */

export type EggReward = { type: "title"; title: string } | { type: "preset"; preset: string; label: string };

export interface EggDef {
  id: string;
  title: string;
  /** Shown as "???" + hint until found. */
  hint: string;
  reward: EggReward;
  group: "global" | "search";
}

const title = (t: string): EggReward => ({ type: "title", title: t });

export const EGGS: EggDef[] = [
  { id: "konami", title: "Cheat Code", hint: "Some codes never die.", reward: title("Cheat Code"), group: "global" },
  { id: "developer", title: "You are now a developer!", hint: "Knock on the masthead. Keep knocking.", reward: title("Developer"), group: "global" },
  { id: "corner", title: "Perfect corner", hint: "Walk away long enough and wait for the perfect angle.", reward: title("Corner Case"), group: "global" },
  { id: "pi-time", title: "π o'clock", hint: "Some minutes are more irrational than others.", reward: title("π Badge"), group: "global" },
  { id: "leet", title: "1337", hint: "Answer at an elite hour.", reward: title("Leet"), group: "global" },
  { id: "fermat", title: "Fermat's margin", hint: "Some notes run out of room.", reward: title("Marginalia"), group: "global" },
  { id: "qed", title: "Tombstone", hint: "Finish your argument the old-fashioned way.", reward: title("Q.E.D."), group: "global" },
  { id: "quack", title: "Rubber duck", hint: "Explain it to someone who only knows one word.", reward: title("Duck Debugger"), group: "global" },
  {
    id: "vaporwave",
    title: "A E S T H E T I C",
    hint: "Collect enough secrets and the sunset turns pink.",
    reward: { type: "preset", preset: "vaporwave", label: "Vaporwave theme" },
    group: "global",
  },
  { id: "search-42", title: "The Answer", hint: "Ask the browser the ultimate question.", reward: title("Hitchhiker"), group: "search" },
  { id: "search-1729", title: "Taxicab number", hint: "A rather dull number, said Hardy.", reward: title("Taxicab"), group: "search" },
  { id: "search-xyzzy", title: "Nothing happens", hint: "A magic word from a very old cave.", reward: title("Adventurer"), group: "search" },
  { id: "search-sudo", title: "Nice try", hint: "Ask the browser nicely, with privileges.", reward: title("Not in the Sudoers File"), group: "search" },
  { id: "search-rm-rf", title: "Not today", hint: "The most dangerous search of all.", reward: title("Daredevil"), group: "search" },
  { id: "search-hello-world", title: "Hello, world", hint: "Every program starts by saying it.", reward: title("First Program"), group: "search" },
  { id: "search-p-np", title: "Millennium problem", hint: "Settle the big one in the search box.", reward: title("Optimist"), group: "search" },
  { id: "search-riemann", title: "Still open", hint: "Search for a famous hypothesis.", reward: title("Zeta Hunter"), group: "search" },
  { id: "search-erdos", title: "Erdős number", hint: "Look up the most prolific collaborator.", reward: title("Collaborator"), group: "search" },
  { id: "search-coffee", title: "Theorem machine", hint: "Search for fuel.", reward: title("Theorem Machine"), group: "search" },
  { id: "search-euler", title: "One line", hint: "Search for the most beautiful equation.", reward: title("Identity"), group: "search" },
  { id: "search-barrel-roll", title: "Barrel roll", hint: "Ask the browser to perform a manoeuvre.", reward: title("Ace Pilot"), group: "search" },
];

export const VAPORWAVE_ID = "vaporwave";
export const VAPORWAVE_THRESHOLD = 10;

/** True when enough secrets are found to unlock the hidden Vaporwave preset. */
export function shouldUnlockVaporwave(secrets: Iterable<string>, threshold = VAPORWAVE_THRESHOLD): boolean {
  let count = 0;
  for (const s of secrets) {
    if (s === VAPORWAVE_ID) return false;
    count++;
  }
  return count >= threshold;
}

export function rewardLabel(r: EggReward): string {
  return r.type === "title" ? `Title: ${r.title}` : `Unlocks the ${r.label}`;
}
