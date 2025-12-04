import { Link } from "react-router";
import { useState } from "react";
import { Button } from "~/components/ui/button";
import { FieldGroup, Field, FieldLabel} from "~/components/ui/field";
import { Textarea } from "~/components/ui/textarea";

export async function clientLoader({ params }) {
  const res = await fetch(`/api/job-boards/${params.jobBoardId}/job-posts`);
  const job_board_id = params.jobBoardId
  const jobPosts = await res.json();
  return { jobPosts ,job_board_id};
}

export default function JobPosts({ loaderData }) {
  const [is_reccomended , setRecom] = useState(false)
  const [triggered_id,setId] = useState(1)
  
  const [button_state,setButton] = useState("Reccomend the Applicant")
  const [payload,setPayload] = useState({
    "first_name":"",
    "last_name":"",
    "id":"",
    "email":"",
    "resume":""
  })
  const reccomendNew = async (job_id:number | string) => {
    setButton("Finding ...")
    const resp = await fetch(`/api/job-posts/${job_id}/recommend`)
    const response = await resp.json()
    
    if (resp.ok){
      setRecom(true)
      setId(job_id)
      setPayload(response)
    }
    else{
      setButton("Failed")
    }
    setButton("Reccomend the Applicant")
  }
  return (
    <div className="w-full mx-auto mt-10 px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Job Posts</h1>

        <Link
            to={`/job-post/new/${loaderData.job_board_id}`}
            className="px-4 py-2 text-sm font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 transition"
        >
            Add New Job
        </Link>
      </div>
      <div className="space-y-6">
        {loaderData.jobPosts.map((jobPost) => (
          <div
            key={jobPost.id}
            className="rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow bg-white"
          >
            <h2 className="text-xl font-semibold text-blue-600 hover:text-blue-800">
              <Link to={`/job-application/new/${jobPost.id}`}>
                {jobPost.title}
              </Link>
            </h2>

            <p className="text-gray-600 mt-2">{jobPost.description}</p>

            <div className="mt-4">
              <Link
                to={`/job-application/new/${jobPost.id}`}
                className="inline-block px-4 py-2 text-sm font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 transition"
              >
                Apply Now
              </Link>

              <div className="text-right">
                <Button
                  type="button"
                  onClick={() => reccomendNew(jobPost.id)}
                  className="inline-block px-4 py-2 text-sm font-medium rounded-md bg-cyan-600 text-white hover:bg-blue-700 transition"
                >
                  {is_reccomended && triggered_id === jobPost.id ? button_state : "Reccomend the Applicant"}
                </Button>
              </div>
              
              {is_reccomended && triggered_id === jobPost.id ? (
                <div className="flex justify-end mt-4">
                  <div className="w-100 bg-white shadow-lg border border-gray-200 rounded-xl p-4 space-y-3">
                    <FieldGroup>

                      {/* <Field>
                        <FieldLabel className="w-full font-medium text-gray-700">
                          First Name:
                        <input
                          placeholder="First Name"
                          value={payload.first_name}
                          readOnly
                          className="w-full border rounded-md px-3 py-2 bg-gray-50 text-sm"
                        />
                        </FieldLabel>
                      </Field>

                      <Field>
                        <FieldLabel className="font-medium text-gray-700">
                          Last Name:
                        <input
                          placeholder="Last Name"
                          value={payload.last_name}
                          readOnly
                          className="w-full border rounded-md px-3 py-2 bg-gray-50 text-sm"
                        />
                        </FieldLabel>
                      </Field>

                      <Field>
                        <FieldLabel className="font-medium text-gray-700">
                          Email:
                        <input
                          placeholder="Email"
                          value={payload.email}
                          readOnly
                          className="w-full border rounded-md px-3 py-2 bg-gray-50 text-sm"
                        />
                        </FieldLabel>
                      </Field>

                      <Field>
                        <FieldLabel className="font-medium text-gray-700">
                          Applicant ID:
                        <input
                          placeholder="ID"
                          value={payload.id}
                          readOnly
                          className="w-full border rounded-md px-3 py-2 bg-gray-50 text-sm"
                        />
                        </FieldLabel>
                      </Field> */}

                      <Field>
                        <FieldLabel className="font-medium text-gray-700">
                          Resume Link:
                      <Link
                      to = {`${window.location.origin}/${payload.resume}`}
                      target="_blank" 
                      rel="noopener noreferrer"
                      >
                        <input
                          placeholder="link"
                          value={payload.resume}
                          readOnly
                          className="w-full border rounded-md px-3 py-2 bg-gray-50 text-sm"
                        />
                        </Link>
                         </FieldLabel>
                      </Field>

                    </FieldGroup>
                  </div>
                </div>
              ) : null}
            </div>
            
          </div>
        ))}
      </div>
    </div>
  );
}
