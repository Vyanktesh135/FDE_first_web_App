import { layout,route,type RouteConfig } from "@react-router/dev/routes";

export default [
    layout('layout/default.tsx',
    [
        route('/', 'routes/home.tsx'),
        route('/job-boards', 'routes/job_boards.tsx'),
        route('/job-boards/:jobBoardId/job-posts', 'routes/job_post.tsx'),
        route('/job-boards/new','routes/job_boards_new.tsx'),
        route('/job-boards/update/logo','routes/job_board_update.tsx')
    ])
]satisfies RouteConfig;
