import { Form, Link, redirect, useLocation } from "react-router";
import type { Route } from "../+types/root";
import { Field, FieldGroup, FieldLabel, FieldLegend } from "~/components/ui/field";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button";

export async function clientAction({ request }: Route.ClientActionArgs){
    const formData = await request.formData()
    await fetch('/api/job-application',{
        method: 'POST',
        body: formData
    })
    return redirect('/job-boards')
}
export default function NewJobBoardForm(_: Route.ComponentProps) {
  const { search }  = useLocation()
  const params = new URLSearchParams(search);
  const job_post_id = params.get("id");
  return (
    <div className="w-full max-w-md">
      <Form method="post" encType="multipart/form-data">
        <FieldGroup>
          <FieldLegend>Add New Job Application</FieldLegend>
          <Field>
            <FieldLabel htmlFor="first_name">
              First Name 
            </FieldLabel>
            <Input
            id="first_name"
            name="first_name"
            type="test"
            required
            />
          </Field>
          
          <Field>
            <FieldLabel htmlFor="last_name">
              Last Name
            </FieldLabel>
            <Input
            id="last_name"
            name="last_name"
            type="text"
            required
            />
          </Field>

          <Field>
            <FieldLabel htmlFor="email">
              Email
            </FieldLabel>
            <Input
            id = "email"
            name = "email"
            type = "email"
            required
            />
          </Field>
          
          <Field>
            <FieldLabel htmlFor="resume">
              Resume
            </FieldLabel>
            <Input
            id = "resume"
            name = "resume"
            type = "file"
            required
            />
          </Field>
          <Field>
            <input
            name = 'job_post_id'
            id = 'job_post_id'
            type='hidden'
            value={`${job_post_id}`}/>
          </Field>

          <Button type="submit">Submit</Button>
        </FieldGroup>
      </Form>
    </div>
  );
}