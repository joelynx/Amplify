/**
 * Saved loadouts: name the current combination, switch between saved ones,
 * and share them as a short code (club members can paste each other's
 * codes; a code only names items, so nothing is unlocked by it).
 */

import { useState } from "react";
import { Copy, Trash2 } from "lucide-react";

import { normalizeLoadout, resolve } from "../../appearance/registry";
import { useAppearance } from "../../appearance/store";
import type { Loadout } from "../../appearance/types";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";

const PREFIX = "AMP1:";

export function encodeLoadout(l: Loadout): string {
  const short = Object.fromEntries(Object.entries(l).map(([k, v]) => [k, v.slice(v.indexOf(".") + 1)]));
  return PREFIX + btoa(unescape(encodeURIComponent(JSON.stringify(short))));
}

export function decodeLoadout(code: string): Loadout | null {
  const c = code.trim();
  if (!c.startsWith(PREFIX)) return null;
  try {
    const short = JSON.parse(decodeURIComponent(escape(atob(c.slice(PREFIX.length))))) as Record<string, string>;
    return normalizeLoadout(Object.fromEntries(Object.entries(short).map(([k, v]) => [k, `${k}.${v}`])));
  } catch {
    return null;
  }
}

export function SavedLoadouts() {
  const st = useAppearance();
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  const save = () => {
    const n = name.trim();
    if (!n) return;
    st.saveLoadout(n);
    setName("");
    setMsg(`Saved "${n}".`);
  };

  const copy = async (l: Loadout) => {
    try {
      await navigator.clipboard.writeText(encodeLoadout(l));
      setMsg("Code copied.");
    } catch {
      setMsg(encodeLoadout(l));
    }
  };

  const importCode = () => {
    const l = decodeLoadout(code);
    if (!l) {
      setMsg("That code isn't a loadout code.");
      return;
    }
    st.useLoadout({ name: "imported", loadout: l });
    setCode("");
    setMsg("Loadout applied. Save it to keep it.");
  };

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card title="Save the current look">
        <div className="flex gap-2">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name, e.g. Late night" onKeyDown={(e) => e.key === "Enter" && save()} />
          <Button variant="primary" onClick={save} disabled={!name.trim()}>
            Save
          </Button>
        </div>
        <div className="mt-4 space-y-2">
          <div className="text-sm font-medium">Paste a loadout code</div>
          <div className="flex gap-2">
            <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="AMP1:…" />
            <Button onClick={importCode} disabled={!code.trim()}>
              Apply
            </Button>
          </div>
        </div>
        {msg && <p className="mt-3 break-all text-xs text-muted">{msg}</p>}
      </Card>
      <Card title="Saved">
        {st.saved.length === 0 ? (
          <p className="text-sm text-muted">Nothing saved yet.</p>
        ) : (
          <ul className="divide-y divide-border">
            {st.saved.map((s) => (
              <li key={s.name} className="flex items-center gap-2 py-2 text-sm">
                <div className="min-w-0 flex-1">
                  <div className="font-medium">{s.name}</div>
                  <div className="truncate text-xs text-muted">
                    {["palette", "chrome", "sfx", "room"]
                      .map((slot) => resolve(s.loadout, slot as keyof Loadout)?.name)
                      .filter(Boolean)
                      .join(" · ")}
                  </div>
                </div>
                <Button size="sm" variant="primary" onClick={() => st.useLoadout(s)}>
                  Use
                </Button>
                <Button size="sm" variant="ghost" onClick={() => void copy(s.loadout)} aria-label={`Copy code for ${s.name}`}>
                  <Copy className="h-4 w-4" />
                </Button>
                <Button size="sm" variant="ghost" onClick={() => st.deleteLoadout(s.name)} aria-label={`Delete ${s.name}`}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </li>
            ))}
          </ul>
        )}
        <Button size="sm" variant="outline" className="mt-3" onClick={() => void copy(st.loadout)}>
          <Copy className="h-4 w-4" /> Copy a code for the current look
        </Button>
      </Card>
    </div>
  );
}
