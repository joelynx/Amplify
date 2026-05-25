import { Link } from "react-router-dom";
import { Button } from "../components/ui/Button";

/** Welcome screen. Step 4 ships only an Enter → Generate link; the other
 * navlinks (About / Theme / Subjects / Tutorial) land in later steps. */
export default function WelcomePage() {
  return (
    <main className="flex h-full items-center justify-center px-6">
      <div className="space-y-6 text-center">
        <div className="space-y-2">
          <h1 className="text-4xl font-semibold tracking-tight">Amplify</h1>
          <p className="text-sm text-muted">Practice problem sets, generated from a curated bank.</p>
        </div>
        <Link to="/generate">
          <Button variant="primary" size="md">
            Enter
          </Button>
        </Link>
      </div>
    </main>
  );
}
