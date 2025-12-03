import { Field,FieldGroup,FieldLabel, FieldLegend } from "~/components/ui/field";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button";
import { Textarea } from "~/components/ui/textarea";
import type { Route } from "../+types/root";
import { Form,redirect } from "react-router";
import { useState } from "react";
import { Link } from "react-router";

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  const { job_board_id } = params;
  return { job_board_id };
}

export async function clientAction({request}: Route.ClientActionArgs){
    console.log("In client action ..!")
    const formData = await request.formData()
    await fetch("/api/job-posts", {
        method : "POST",
        body: formData
    })

    return redirect(`/job-boards/${formData.get("job_board_id")}/job-posts`)
}

export default function CreateNewJob({loaderData}){

    const [title,setTitle] = useState()
    const [description,setDescription] = useState()
    const [button_name,setButton] = useState("Review")
    const [new_desc,setDesc] = useState("Reviewed Desc")
    const [is_reviewd,setStatus] = useState(false)
    const [bg_color,setBg] = useState("blue")
    const [button_status,setButStatus] = useState(false)
    const [revised_desc,setRevised] = useState("")

    const handleReview = async () => {
        console.log("In handler")
        try {
            setBg("green")
            setButton("Analysing ...")
            setButStatus(true)
            const form_data = new FormData()
            form_data.append("title",title)
            form_data.append("description",description)
            form_data.append("job_board_id",loaderData.job_board_id)
            
            const res = await fetch('/api/review-job-description', {
                method : 'POST',
                body: form_data
            })

            if (!res.ok) {
                throw new Error("Failed to fetch the data")
            }

            const data = await res.json()
            setStatus(true)
            setDesc(data.description ?? "")
            setButton("Submit")
            setRevised(data.revised_description ?? "")
        }
        catch(err){
            console.error(err);
        }
    }

    return (
        <>
        <div className="w-full max-w-md mx-auto mt-10 bg-white shadow-md rounded-xl p-6 border border-gray-200">

        <Form method="post" encType="multipart/form-data" className="space-y-6">
            <FieldGroup className="space-y-6">

                {/* Legend */}
                <FieldLegend className="text-xl font-semibold text-gray-800 mb-4">
                    Add The New Job
                </FieldLegend>

                {/* Title */}
                <Field className="flex flex-col gap-1">
                    <FieldLabel htmlFor="title" className="text-sm font-medium text-gray-700">
                        Title
                    </FieldLabel>
                    <Input
                        id="title"
                        type="text"
                        name="title"
                        placeholder="Software Engineer"
                        className="border rounded-lg px-3 py-2"
                        onChange={(e) => setTitle(e.target.value)}
                        value={title}
                        required
                    />
                </Field>

                {/* Description */}
                <Field className="flex flex-col gap-1">
                    <FieldLabel htmlFor="description" className="text-sm font-medium text-gray-700">
                        Description
                    </FieldLabel>
                    <Textarea
                        id="description"
                        // type="text"
                        name="description"
                        placeholder= "Job Description"
                        className="border rounded-lg px-3 py-2"
                        onChange={(e) => setDescription(e.target.value)}
                        value={description}
                        required
                    />
                </Field>

                {/* Hidden job board id */}
                <Input
                    id="job_board_id"
                    name="job_board_id"
                    type="hidden"
                    value={`${loaderData.job_board_id}`}
                />

                {/* Review Section */}
                {is_reviewd ? (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <Field>
                            <FieldLabel className="text-sm font-medium text-gray-700">
                                Review Comments:
                            </FieldLabel>
                            <Textarea
                                name="review_desc"
                                id="review_desc"
                                value={new_desc}
                                readOnly
                                className="bg-gray-100 border rounded-lg"
                            />
                        </Field>
                    </div>
                ) : (
                    <Input
                        type="hidden"
                        name="review_desc"
                        id="review_desc"
                        value={new_desc}
                    />
                )}

                {/* Buttons */}
                
                    {is_reviewd ? (
                        <Field orientation="horizontal" className="mt-4">
                        <Button
                            type="submit"
                            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                        >
                            {button_name}
                        </Button>
                        <Button
                            type="button"
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-green-700"
                            onClick={() => setDescription(revised_desc)}
                        >
                            Fix For Me
                        </Button>
                        <Link to={`/job-boards/${loaderData.job_board_id}/job-posts`}>
                        <Button>Cancel</Button></Link>
                        </Field>
                    ) : (
                        <Field orientation="horizontal" className="mt-4">
                        <Button
                            type="button"
                            onClick={handleReview}
                            disabled={button_status}
                            className={`px-4 py-2 bg-${bg_color}-600 text-white rounded-md hover:bg-blue-700`}
                        >
                            {button_name}
                        </Button>
                        <Link to={`/job-boards/${loaderData.job_board_id}/job-posts`}>
                        <Button>Cancel</Button></Link>
                        </Field>
                    )}

                    

            </FieldGroup>
        </Form>

        </div>
        </>
    )
}
