import { Form, Link, redirect, useLocation } from "react-router";
import type { Route } from "../+types/root";
import { Field, FieldGroup, FieldLabel, FieldLegend } from "~/components/ui/field";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button";
import {
  Avatar,
  AvatarImage,
  AvatarFallback,
} from "~/components/ui/avatar";

export async function clientAction({ request }: Route.ClientActionArgs){
   
    const formData = await request.formData()
    await fetch(`/api/job-boards/logo/${formData.get("id")}`,{
        method: 'PUT',
        body: formData
    })
    return redirect('/job-boards')
}
export default function NewJobBoardForm(_: Route.ComponentProps) {
    const { search } = useLocation();
    const params = new URLSearchParams(search);
    const id = params.get("id");
    const slug = params.get("slug");
    const logo = params.get("logo");
  return (
    <div className="w-full max-w-md">
      <Form method="post" encType="multipart/form-data">
        <FieldGroup>
          <FieldLegend>Update Job Board</FieldLegend>
          <Field>
            <FieldLabel htmlFor="slug">
              Slug
            </FieldLabel>
            <Input
              id="slug"
              name="slug"
              placeholder={`${slug}`}
              required
              readOnly
            />
          </Field>
          <Field>
            <FieldLabel htmlFor="logo">
              Current Logo
            </FieldLabel>
            <Avatar className="h-20 w-20 border border-slate-700">
                {logo ? (
                <AvatarImage 
                    src={`/${logo}`}
                    // alt={slug}
                    className="object-contain"
                />
                ) : (
                <AvatarFallback>
                    {slug?.slice(0, 2) || "JB"}
                </AvatarFallback>
                )}
            </Avatar>

            <FieldLabel htmlFor="logo">
              New Logo
            </FieldLabel>
            <Input
              id="logo"
              name="logo"
              type="file"
              required
            />
            <input type="hidden" name="id" value={`${id}`} />
          </Field>
          <div className="float-right">
            <Field orientation="horizontal">
              <Button type="submit">Submit</Button>
              <Button variant="outline" type="button">
                <Link to="/job-boards">Cancel</Link>
              </Button>
            </Field>
          </div>
        </FieldGroup>
      </Form>
      {/* <Link to = '/job-boards'>Go </> */}
    </div>
  );
}