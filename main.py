from fastapi import FastAPI,HTTPException
from fastapi.responses import JSONResponse
import traceback
from fastapi import BackgroundTasks
from fastapi import Request,Response,status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import UploadFile,File,Form
import os
from fastapi.responses import RedirectResponse,FileResponse
import re
from sqlalchemy import text
from db import get_db_session
from models import JobBoard,JobPost
import logging
from typing import Annotated
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from config import settings
from supabase import Client,create_client
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

app = FastAPI()
class server_exception(Exception):
  def __init__(self,name):
    self.name = name

#Mounting Static Assets
if not settings.PRODUCTION:
  app.mount("/static",StaticFiles(directory="static"),name = "static")
# templates = Jinja2Templates(directory="templates")

supabase: Client = create_client(str(settings.SUPABASE_URL), settings.SUPABASE_KEY)

def upload_file(bucket_name, path, contents, content_type):
  if settings.PRODUCTION:
    print("Writing in PROD SUPABASE")
    response = supabase.storage.from_(bucket_name) \
                .upload(path, contents, {"content-type": content_type, "upsert": "true"})
    return f"{str(settings.SUPABASE_URL)}/storage/v1/object/public/{response.full_path}"
  else:
    with open(path, "wb") as f:
        f.write(contents)
    # Return correct web-accessible URL
    result_path = path.replace("\\","/")
    return result_path

class Calc_data(BaseModel):
  a: int = Field(...,ge=1,le=3)
  b: int = Field(...,ge=1,le=3)

class JobBoardForm(BaseModel):
  slug: str = Field(...,min_length=3,max_length=20)
  logo: UploadFile = Field(...)

  @field_validator('slug')
  @classmethod
  def to_lowercase(cls,v):
    return v.lower()

@app.exception_handler(server_exception)
async def server_exception_handler(request: Request, exc: server_exception):
  error_msg = traceback.format_exc()
  print(error_msg)

  details = {
    "method" : request.method,
    "url": request.url,
    "client": request.client.host if request.client else None,
    "error": str(exc),
    "traceback": error_msg
  }

  background_task = BackgroundTasks()
  #TODO
  #Sending the alert is pending
  # background_task.add_task(send_email_alert,details)
  # background_task.add_task(send_teams_alert,details)
  return JSONResponse(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    content = {"error":"Internal server error from Internal Exception"},
    background=background_task
  )

@app.get("/api/health")
async def health():
  status = "Down"
  try:
    with get_db_session() as session:
        session.execute(text("SELECT 1"))
        print("All good!")
        status = "OK"
  except Exception as e:
    # raise server_exception(name = "Internal Server Error")
    print(e)
    status = "Down"
  
  return {"status": "OK","Database":status}

@app.get("/api/job_board")
async def get_job():
  try:
    with get_db_session() as session:
      job_board = session.query(JobBoard).all()
      return job_board
  except Exception as e:
    print("Failed to execute query ..!",e)
    raise server_exception("Internal Server Error")

@app.get("/", response_class = HTMLResponse,name="home")
async def home(request: Request):
  # return templates.TemplateResponse("index.html",{"request":request})
  return {"Message":"From Hello Page"}

@app.get("/render_test")
async def render_test():
  return {"message" : "test completed"}

@app.post("/api/add")
async def addition(payload: Calc_data):
  print(payload)
  return {"result" : payload.a + payload.b}

@app.post("/api/multiply")
async def multiply(payload: Calc_data):
  print(payload)
  return {"result" : payload.a * payload.b}

# @app.get("/api/job-boards/upload",response_class=HTMLResponse,name="get_logo")
# async def upload(request: Request):
#   return templates.TemplateResponse("update_logo.html",{"request":request})

@app.post("/api/job-boards/update_logo",response_class = HTMLResponse,name="update_logo")
async def updated_logo(
  request:Request,
  companyName:str = Form(...),
  companyLogo:UploadFile = File(...)):
  
  upload_folder = os.path.join("static","images")
  os.makedirs(upload_folder,exist_ok=True)

  allowed_extension = {"png","jpg","jpeg","gif"}

  company_name = companyName.strip().lower()
  if not company_name:
    url = request.url_for("get_logo")
    return RedirectResponse(
      f"{url}?error=Please%20enter%20company%20name.",
      status_code=304
    )

  if not companyLogo:
    url = request.url_for("get_logo")
    return RedirectResponse(
      f"{url}?error=%20Please%20provide%logo.",
      status_code=304
    )

  slugify_name = company_name.replace(" ","").replace("_","").replace(".","")
  slugify_name = re.sub(r"[^a-z0-9_]", "", slugify_name)

  extension = companyLogo.filename.split(".")[1]
  if extension not in allowed_extension:
    url = request.url_for("get_logo")
    return RedirectResponse(
      f"{url}?error=%20{extension}%20Extension%20is%20not%20allowed.",
      status_code=404
    )
  
  file_path = f"{slugify_name}.{extension}"
  save_path = os.path.join(upload_folder,file_path)

  with open(save_path,"wb") as buffer:
    content = await companyLogo.read()
    buffer.write(content)
  
  url = request.url_for("home")
  msg = f"Saved logo as /static/images/{save_path}"
  return RedirectResponse(f"{url}?msg={msg.replace(' ', '%20')}", status_code=303)

#Query Parameters
# @app.get("/api/job-boards")
# async def job_boards(name:str,title:str,request: Request):
#   try:
#     print("Name of Company",name)
#     acme_title = ["Customer Support Executive","Project Manager"]  
#     bcg_title = ["Technical Architect","Junior Software Developer"]
#     atlas = [
#       # {"title": "Customer Support Executive"},
#       {
#           "title": "Customer Support Executive",
#           "description": "Responsible for assisting customers by resolving product or service inquiries, providing accurate information, handling complaints, and ensuring high customer satisfaction through effective communication and problem-solving."
#       },
#       {
#           "title": "Project Manager",
#           "description": "Oversees project planning, execution, monitoring, and delivery while managing teams, resources, budgets, and timelines. Ensures project objectives are met, risks are mitigated, and stakeholders are consistently updated."
#       },
#       {
#           "title": "Software Engineer",
#           "description": "Designs, develops, tests, and maintains software applications. Collaborates with cross-functional teams to build reliable, scalable, and efficient systems."
#       },
#       {
#           "title": "Data Analyst",
#           "description": "Collects, processes, and analyzes data to uncover trends, support business decisions, and generate actionable insights using statistical and analytical tools."
#       },
#       {
#           "title": "Human Resources Executive",
#           "description": "Manages recruitment, onboarding, employee relations, performance evaluations, and compliance to maintain a healthy organizational environment."
#       },
#       {
#           "title": "Digital Marketing Specialist",
#           "description": "Plans and executes digital marketing campaigns, manages social media presence, analyzes campaign performance, and drives online engagement and brand awareness."
#       },
#       {
#           "title": "UI/UX Designer",
#           "description": "Creates user-centric designs by conducting research, building wireframes, and developing intuitive interfaces that enhance the overall user experience."
#       },
#       {
#           "title": "Sales Manager",
#           "description": "Develops and executes sales strategies, manages sales teams, monitors performance, builds client relationships, and ensures revenue targets are achieved."
#       },
#       {
#           "title": "Network Administrator",
#           "description": "Maintains and monitors computer networks, ensures system stability and security, troubleshoots network issues, and manages network hardware and software."
#       },
#       {
#           "title": "Content Writer",
#           "description": "Produces clear, engaging, and SEO-friendly content for blogs, websites, marketing materials, and social media to support brand communication goals."
#       },
#       {
#           "title": "Accountant",
#           "description": "Handles financial records, prepares reports, manages budgets, ensures compliance with financial regulations, and supports audits and tax preparation."
#       },
#       {
#           "title": "Business Development Executive",
#           "description": "Identifies new business opportunities, builds partnerships, expands the client base, and contributes to strategic growth initiatives."
#       }
#     ]
#     result = []
#     if name == "acme":
#       for job in acme_title:
#         result.append({"title":job})
      
#     elif name == "bcg":
#       for job in bcg_title:
#         result.append({"title":job})
      
#     elif name == "atlas":
#       for item in atlas:
#         result.append({
#           "title" : item["title"],
#           "description": item["description"]
#         })
#     else:
#       result.append({
#         "title":"No title to display please provide correct name"
#       })
    
#     return templates.TemplateResponse(
#       "job_boards.html",
#       {
#         "request":request,
#         "details": result,
#         "company": name,
#         "src_title":title,
#       }
#     )
  
#   except Exception as e:
#     print("Error while processing the request",e)
#     raise HTTPException(
#       status_code=500,
#       detail = f"Not able to process the request at the moment"
#     )
  
#   return {"title":""}

#Path Parameters
@app.get("/api/job-boards/{name}")
async def job_boards(name:str,response:Response ):
  try:
    # print("Name of Company",name)
    # jd = {
    #   "acme":[{"title":"Customer Support Executive"},{"title":"Project Manager"}] , 
    #   "bcg":[{"title":"Technical Architect"},{"title":"Junior Software Developer"}],
    #   "atlas": [
            
    #         {
    #             "title": "Customer Support Executive",
    #             "description": "Responsible for assisting customers by resolving product or service inquiries, providing accurate information, handling complaints, and ensuring high customer satisfaction through effective communication and problem-solving."
    #         },
    #         {
    #             "title": "Project Manager",
    #             "description": "Oversees project planning, execution, monitoring, and delivery while managing teams, resources, budgets, and timelines. Ensures project objectives are met, risks are mitigated, and stakeholders are consistently updated."
    #         },
    #         {
    #             "title": "Software Engineer",
    #             "description": "Designs, develops, tests, and maintains software applications. Collaborates with cross-functional teams to build reliable, scalable, and efficient systems."
    #         },
    #         {
    #             "title": "Data Analyst",
    #             "description": "Collects, processes, and analyzes data to uncover trends, support business decisions, and generate actionable insights using statistical and analytical tools."
    #         },
    #         {
    #             "title": "Human Resources Executive",
    #             "description": "Manages recruitment, onboarding, employee relations, performance evaluations, and compliance to maintain a healthy organizational environment."
    #         },
    #         {
    #             "title": "Digital Marketing Specialist",
    #             "description": "Plans and executes digital marketing campaigns, manages social media presence, analyzes campaign performance, and drives online engagement and brand awareness."
    #         },
    #         {
    #             "title": "UI/UX Designer",
    #             "description": "Creates user-centric designs by conducting research, building wireframes, and developing intuitive interfaces that enhance the overall user experience."
    #         },
    #         {
    #             "title": "Sales Manager",
    #             "description": "Develops and executes sales strategies, manages sales teams, monitors performance, builds client relationships, and ensures revenue targets are achieved."
    #         },
    #         {
    #             "title": "Network Administrator",
    #             "description": "Maintains and monitors computer networks, ensures system stability and security, troubleshoots network issues, and manages network hardware and software."
    #         },
    #         {
    #             "title": "Content Writer",
    #             "description": "Produces clear, engaging, and SEO-friendly content for blogs, websites, marketing materials, and social media to support brand communication goals."
    #         },
    #         {
    #             "title": "Accountant",
    #             "description": "Handles financial records, prepares reports, manages budgets, ensures compliance with financial regulations, and supports audits and tax preparation."
    #         },
    #         {
    #             "title": "Business Development Executive",
    #             "description": "Identifies new business opportunities, builds partnerships, expands the client base, and contributes to strategic growth initiatives."
    #         }
    #       ]
    #   }
    # # if name in jd.keys():
    # #   return jd[name]
    # # else:
    # #   response.status_code = 404
    # #   return {"error": "Not Found - Resource not available."}
    # return jd[name]
    with get_db_session() as session:
      jobPosts = session.query(JobPost).join(JobPost.job_board).filter(JobBoard.slug.__eq__(name)).all()
      # print(jobPosts.statement.compile(compile_kwargs={"literal_binds": True}))
      return jobPosts
  except Exception as e:
    print("Error while processing the request",e)
    raise server_exception(name = "Internal Server Error")
  return {"title":""}

@app.get("/api/vite_testing")
async def vite_testing():
  try:
    name = "atlas"
    print("Name of Company",name)
    jd = {
      "acme":[{"title":"Customer Support Executive"},{"title":"Project Manager"}] , 
      "bcg":[{"title":"Technical Architect"},{"title":"Junior Software Developer"}],
      "atlas": [
            
            {
                "title": "Customer Support Executive",
                "description": "Responsible for assisting customers by resolving product or service inquiries, providing accurate information, handling complaints, and ensuring high customer satisfaction through effective communication and problem-solving."
            },
            {
                "title": "Project Manager",
                "description": "Oversees project planning, execution, monitoring, and delivery while managing teams, resources, budgets, and timelines. Ensures project objectives are met, risks are mitigated, and stakeholders are consistently updated."
            },
            {
                "title": "Software Engineer",
                "description": "Designs, develops, tests, and maintains software applications. Collaborates with cross-functional teams to build reliable, scalable, and efficient systems."
            },
            {
                "title": "Data Analyst",
                "description": "Collects, processes, and analyzes data to uncover trends, support business decisions, and generate actionable insights using statistical and analytical tools."
            },
            {
                "title": "Human Resources Executive",
                "description": "Manages recruitment, onboarding, employee relations, performance evaluations, and compliance to maintain a healthy organizational environment."
            },
            {
                "title": "Digital Marketing Specialist",
                "description": "Plans and executes digital marketing campaigns, manages social media presence, analyzes campaign performance, and drives online engagement and brand awareness."
            },
            {
                "title": "UI/UX Designer",
                "description": "Creates user-centric designs by conducting research, building wireframes, and developing intuitive interfaces that enhance the overall user experience."
            },
            {
                "title": "Sales Manager",
                "description": "Develops and executes sales strategies, manages sales teams, monitors performance, builds client relationships, and ensures revenue targets are achieved."
            },
            {
                "title": "Network Administrator",
                "description": "Maintains and monitors computer networks, ensures system stability and security, troubleshoots network issues, and manages network hardware and software."
            },
            {
                "title": "Content Writer",
                "description": "Produces clear, engaging, and SEO-friendly content for blogs, websites, marketing materials, and social media to support brand communication goals."
            },
            {
                "title": "Accountant",
                "description": "Handles financial records, prepares reports, manages budgets, ensures compliance with financial regulations, and supports audits and tax preparation."
            },
            {
                "title": "Business Development Executive",
                "description": "Identifies new business opportunities, builds partnerships, expands the client base, and contributes to strategic growth initiatives."
            }
          ]
      }
    # if name in jd.keys():
    #   return jd[name]
    # else:
    #   response.status_code = 404
    #   return {"error": "Not Found - Resource not available."}
    return jd[name]  
  except Exception as e:
    print("Error while processing the request",e)
    raise server_exception(name = "Internal Server Error")
  return {"title":""}

# @app.get("/api/job-boards/{job_board_id}/job-posts")
# async def api_company_job_board(job_board_id):
#   with get_db_session() as session:
#      jobPosts = session.query(JobPost).filter(JobPost.job_board_id.__eq__(job_board_id)).all()
#      return jobPosts

@app.get('/api/job-boards/{id}/job-posts')
async def api_to_get_jobposts(id:int = 0):
  print('*****************',id,f'Type - {type(id)}******************************')
  with get_db_session() as session:
    # session.query(JobPost).filter() 
    jobPosts = session.query(JobPost).join(JobBoard).filter(JobBoard.id.__eq__(int(id))).all()
    print("\n************* Output is ************ ",jobPosts)
    return jobPosts
  
# @app.post("/api/job-boards")
# async def create_new_job_boards(request: Request):
#   try:
#     body = await request.body()
#     raw_text = body.decode()
#     print(raw_text)
#     print(request.headers.get('content-type'))
#     return JSONResponse(
#       status_code= status.HTTP_200_OK,
#       content= {
#         "message" : "OK"
#       }
#     )
#   except Exception as e:
#     print(e)
#     raise server_exception("Internal Server Error: Failed to create the job_board")
  
# @app.post("/api/job-boards")
# async def create_new_job_boards(slug: Annotated[str, Form()]):
#   try:
#     return {"slug":slug}
#   except Exception as e:
#     print(e)
#     raise server_exception("Internal Server Error: Failed to create the job_board")

@app.post("/api/job-boards")
async def create_new_job_boards(payload: Annotated[JobBoardForm , Form()]):
  try:
    upload_folder = os.path.join("static","images")
    os.makedirs(upload_folder,exist_ok=True)

    allowed_extension = {"png","jpg","jpeg","gif"}

    # file_path = os.path.join(Upload_dir,f"{payload.slug}.png")
    contents = await payload.logo.read()

    extension = payload.logo.filename.split(".")[1]
    if extension not in allowed_extension:  
      raise server_exception("File Format is not correct please share the correct format ..!")
    
    file_path = f"{payload.slug}.{extension}"
    save_path = os.path.join(upload_folder,file_path)
    # print(save_path)
    # with open(save_path,"wb") as buffer:
    #   buffer.write(contents)

    result_path = upload_file(settings.SUPABASE_BUCKET, save_path, contents, payload.logo.content_type)

    # result_path = save_path.replace("\\","/")

    data = JobBoard(slug = payload.slug, logo = result_path)
    db = get_db_session()
    db.add(data)
    db.commit()
    db.refresh(data)
    return {
      "slug":payload.slug,
      "file_url":result_path
    }
  except Exception as e:
    print(e)
    raise server_exception("Internal Server Error: Failed to create the job_board")

@app.put("/api/job-boards/{item_id}")
async def update_job_boards(item_id:int ,payload: Annotated[JobBoardForm , Form()]):
  try:
    db = get_db_session()
    result = db.query(JobBoard).filter(JobBoard.slug == payload.slug, JobBoard.id == item_id).first()
    if not result:
      return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content = ( {"Details":f"{payload.slug} with item_id {item_id} not present ..!"})
      )
     
    upload_folder = os.path.join("static","images")
    extension = payload.logo.filename.split(".")[1]
    # extension = payload.logo.content_type
    if extension not in {"png","jpg","jpeg","gif"}:
      return JSONResponse(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        content = ( {"Details":"Please provide the correct exensions ['png','jpg','jpeg','gif'] ..!"})
      )
    
    os.makedirs(upload_folder,exist_ok=True)
    file_path = os.path.join(upload_folder,f"{payload.slug}.{extension}")
    contents = await payload.logo.read()

    result_path = upload_file(settings.SUPABASE_BUCKET, file_path, contents, payload.logo.content_type)
    print(result_path)

    result.logo = result_path
    db.add(result)
    db.commit()
    print(result)
    # db.
    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={
        "slug":payload.slug,
        "updated_url":file_path
      } 
    )
  except Exception as e:
    print(e)
    raise server_exception("Internal Server Error: Failed to update the job_board")

@app.delete("/api/job-boards/{item_id}")
async def delete_job_boards(item_id: int):
  try:
    db = get_db_session()
    result = db.query(JobBoard).filter(JobBoard.id == item_id).first()
    
    if not result:
      return JSONResponse(
        status_code=status.HTTP_404_NOT_ACCEPTABLE,
        content = ( {"Details":f"Item_id {item_id} not present ..!"})
      )
    else:
      try:
        file_path = Path(result.logo)
        if file_path.is_file():
          file_path.unlink()
      except Exception as e:
        print(f"Failed to delete file {result.logo}: {e}")
        return server_exception("Failed to delete : Internal Server Error ..!")

      db.delete(result)
      db.commit()
    return JSONResponse(
      status_code = status.HTTP_200_OK,
      content=({"Status":f"{result.slug} is removed ..!"})
    )
  except Exception as e:
    print(e)
    raise server_exception("Internal Server Error: Failed to create the job_board")

app.mount("/assets", StaticFiles(directory="frontend/build/client/assets"))
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
  indexFilePath = os.path.join("frontend", "build", "client", "index.html")
  return FileResponse(path=indexFilePath, media_type="text/html")

