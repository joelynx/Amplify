import { Combobox } from "../ui/Combobox";

interface Props {
  subjects: readonly string[];
  value: string | null;
  onChange: (name: string | null) => void;
}

const ANY = "(Any subject)";

/** Subject combobox with the spec's "(Any subject)" sentinel. */
export function SubjectPicker({ subjects, value, onChange }: Props) {
  return (
    <Combobox
      options={subjects}
      value={value}
      onSelect={(name) => onChange(name)}
      placeholder={ANY}
      sentinel={ANY}
      searchPlaceholder="Search subjects"
      emptyMessage="No subjects yet — create one on the Subjects page"
      className="min-w-[14rem]"
    />
  );
}
