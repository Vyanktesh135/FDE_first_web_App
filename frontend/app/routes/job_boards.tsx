import { Link,useFetcher } from "react-router";
import {
  Avatar,
  AvatarImage,
  AvatarFallback,
} from "~/components/ui/avatar";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "~/components/ui/table";
import { Button } from "~/components/ui/button";
import "../app.css";
import type { Route } from "../+types/root";

export async function clientLoader() {
  const res = await fetch("/api/job_board");
  const job_boards = await res.json();
  return { job_boards };
}

export async function clientAction({request}: Route.ClientActionArgs){
  const formData = await request.formData()
  const jobBoardId = formData.get('job_board_id')
  await fetch(`/api/job-boards/${jobBoardId}`,{
    method: 'DELETE'
  })
}
export default function JobBoards({ loaderData }) {
  const jobBoards = loaderData?.job_boards ?? [];

  const fetcher = useFetcher();
  // placeholder handlers – you can replace with real logic
  const handleEditLogo = (jobBoard: any) => {
    console.log("Edit logo clicked for:", jobBoard);
  };

  const handleDeleteJobBoard = (jobBoard: any) => {
    console.log("Delete job board clicked for:", jobBoard);
  };

  return (
    <div className="min-h-screen bg-slate-950/95 py-10">
      <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4">
        {/* Header */}
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-50">
              JOBIFY
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Manage your job boards, update their logos, or remove ones you no longer use.
            </p>
          </div>

          <Button>
            <Link
              to="/job-boards/new"
              className="inline-flex items-center rounded-lg bg-indigo-500 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
            >
              + Add Job Board
            </Link>
          </Button>
        </header>

        {/* Table Card */}
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/70 shadow-xl backdrop-blur">
          <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
            <p className="text-sm font-medium text-slate-200">
              Connected job boards
            </p>
            {jobBoards.length > 0 && (
              <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-medium text-slate-400">
                {jobBoards.length} board{jobBoards.length > 1 ? "s" : ""}
              </span>
            )}
          </div>

          <Table>
            <TableHeader>
              <TableRow className="border-slate-800">
                <TableHead className="w-[80px] text-slate-400">Logo</TableHead>
                <TableHead className="text-slate-400">Job Board</TableHead>
                <TableHead className="text-right text-slate-400">
                  Actions
                </TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {jobBoards.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={3}
                    className="py-10 text-center text-sm text-slate-500"
                  >
                    No job boards found. Click{" "}
                    <span className="font-medium text-slate-200">
                      “Add Job Board”
                    </span>{" "}
                    to create your first one.
                  </TableCell>
                </TableRow>
              ) : (
                jobBoards.map((jobBoard: any) => {
                  const slug = jobBoard.slug ?? "";
                  const displayName =
                    typeof slug === "string"
                      ? slug.replace(/-/g, " ")
                      : String(slug);

                  return (
                    <TableRow
                      key={jobBoard.id}
                      className="border-slate-800 transition hover:bg-slate-800/60"
                    >
                      {/* Logo */}
                      <TableCell>
                        <Avatar className="h-9 w-9 border border-slate-700 bg-slate-900">
                          {jobBoard.logo ? (
                            <AvatarImage
                              src={jobBoard.logo}
                              alt={slug}
                              className="object-contain"
                            />
                          ) : (
                            <AvatarFallback className="text-xs uppercase text-slate-400">
                              {slug?.slice(0, 2) || "JB"}
                            </AvatarFallback>
                          )}
                        </Avatar>
                      </TableCell>

                      {/* Slug / name */}
                      <TableCell className="align-middle">
                        <Link
                          to={`/job-boards/${jobBoard.id}/job-posts`}
                          className="inline-flex items-center gap-2 text-sm font-medium text-slate-50 hover:text-indigo-400"
                        >
                          <span className="capitalize">{displayName}</span>
                          <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[11px] font-normal text-slate-400">
                            View jobs
                          </span>
                        </Link>
                      </TableCell>

                      {/* Actions */}
                      <TableCell className="align-middle text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEditLogo(jobBoard)}
                            className="inline-flex items-center rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 shadow-sm transition hover:bg-slate-800 hover:text-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
                          >
                          <Link
                          to = {`/job-boards/update/logo?id=${jobBoard.id}&slug=${jobBoard.slug}&logo=${jobBoard.logo}`}>
                          Edit logo
                          </Link>
                          </button>

                          <fetcher.Form method="post"
                          onSubmit={(event) => {
                              const response = confirm(
                                `Please confirm you want to delete this job board '${jobBoard.slug}'.`,
                              );
                              if (!response) {
                                event.preventDefault();
                              }
                            }}
                          >
                          <input name="job_board_id" type="hidden" value={jobBoard.id}></input>
                          <button
                          className="bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-300 shadow-sm transition hover:bg-red-500/20 hover:text-red-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
                          >Delete</button>
                        </fetcher.Form>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}