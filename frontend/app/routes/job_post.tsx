export async function clientLoader({params}) {
    const res = await fetch(`/api/job-boards/${params.jobBoardId}/job-posts`);
    const jobPosts = await res.json()
    return {jobPosts}
}

export default function JobPosts({loaderData}) {
    return (
        <div>
            { loaderData.jobPosts.map((jobPost) =>
                <div>
                    <h2 key={jobPost.id}>{jobPost.title}</h2>
                    <p>{jobPost.description}</p>
                </div>
            )}
        </div>
    )
}