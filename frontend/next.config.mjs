const backend = process.env.LLMROUTE_BACKEND || 'http://127.0.0.1:8001';
export default { async rewrites(){return [{source:'/gateway/:path*',destination:`${backend}/:path*`}]} };
