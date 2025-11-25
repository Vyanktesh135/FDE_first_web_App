import { layout,route,type RouteConfig } from "@react-router/dev/routes";

export default [
    layout('layout/default.tsx',
    [
        route('/', 'routes/home.tsx'),
        route('/job-boards', 'routes/job_boards.tsx'),
        route('/job-boards/:jobBoardId/job-posts', 'routes/job_post.tsx')
    ])
]satisfies RouteConfig;
