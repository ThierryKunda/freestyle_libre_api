import uvicorn

from router_dependencies import *
import env

from routers import user, stats, auth, doc, pages

app = FastAPI()

app.include_router(user.router)
app.include_router(stats.router)
app.include_router(auth.router)
app.include_router(doc.router)
app.include_router(pages.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[env.FRONT_END_APP_URI],
    allow_origin_regex=r'https?://(localhost|127\.0\.0\.1).*',
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(env.PORT))