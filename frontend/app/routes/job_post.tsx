import { Link } from "react-router";

export async function clientLoader({ params }) {
  const res = await fetch(`/api/job-boards/${params.jobBoardId}/job-posts`);
  const job_board_id = params.jobBoardId
  const jobPosts = await res.json();
  return { jobPosts ,job_board_id};
}

export default function JobPosts({ loaderData }) {
  return (
    <div className="max-w-3xl mx-auto mt-10 px-4">
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
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
