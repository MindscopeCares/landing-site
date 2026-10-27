import { ToolPage, FormCard } from "../components/ToolPage";

export default function FacilitySearch() {
  return <ToolPage current="/parents/facilities" eyebrow="Finding local support" title="Facility Search"
    description="Public facility search is not available yet.">
    <FormCard>
      <p role="status">Your school counselor can help you find local providers and review their fit, availability, and credentials.</p>
      <p className="mt-4">Already working with your school in MindScope? <a className="underline" href="https://parents.mindscopecares.com/">Open your parent portal</a> to see referrals shared with your family.</p>
    </FormCard>
  </ToolPage>;
}
