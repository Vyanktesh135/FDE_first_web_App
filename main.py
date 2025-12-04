from fastapi import FastAPI,HTTPException
from fastapi.responses import JSONResponse
import traceback
from fastapi import BackgroundTasks, Depends
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
from models import JobBoard,JobPost,JobApplication
import logging
from typing import Annotated
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from config import settings
from supabase import Client,create_client
import string
import secrets
from auth import authenticate_admin,AdminAuthzMiddleware,AdminSessionMiddleware,delete_admin_session
from emailer import send_email
from sqlalchemy.exc import IntegrityError 
from ai import review_application,ingest_resume_for_recommendataions,get_vector_store,get_recommendation
# from httpx import 
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

app = FastAPI()
app.add_middleware(AdminAuthzMiddleware)
app.add_middleware(AdminSessionMiddleware)

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

def validate_extensions(extension,expected_extention):
  if extension not in expected_extention:
    return JSONResponse(
      status_code=status.HTTP_406_NOT_ACCEPTABLE,
      content={"Message":f"Please provide the file with correct extension {expected_extention}"}
    )
  return True

def secure_random_string(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def insert_to_db(data,session = None):
  try:
    if session:
      db_session = session
    else:
      db_session = get_db_session()
    db_session.add(data)
    db_session.commit()
    db_session.refresh(data)
    print("Data is inserted to DB ..!")
    return True
  except Exception as e:
    print(e)
    raise server_exception("Failed to insert to DB ..!")
  finally:
    if db_session:
      db_session.close()
      print("Session has been closed")
 
def job_is_closed(id):
  try:
    db_session = get_db_session()
    result = db_session.query(JobPost).filter(JobPost.id == id).first()
    if result:
      return {
        "status": True if result.job_post_status == 'closed' else False,
        "post": result.title
      }
    else:
      return {
        "status": True,
        "post": "unknown"
      }
  except Exception as e:
    print(e)
    raise server_exception("Failed to check the Job status")
  finally:
    if db_session:
      db_session.close()
      print("Session closed ..!")

def get_details(object):
  try:
    db_session = get_db_session()
    result = db_session.query(object).all()
    return result
  except Exception as e:
    print(e)
    raise server_exception(f"Failed to get the data from {object}")
  finally:
    if db_session:
      db_session.close()
      print("Session is closed ..!")  

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

class JobBoardUpdateSlug(BaseModel):
  slug: str = Field(...,min=3,max_length=20)
  @field_validator('slug')
  @classmethod
  def to_lowercase(cls,v):
    return v.lower()

class JobBoardUpdateLogo(BaseModel):
  logo: UploadFile = Field(...,)

class job_application(BaseModel):
  job_post_id :int = Field(...,ge=1,le=500)
  first_name :str =  Field(...,min_length=3,max_length=20)
  last_name :str =  Field(...,min_length=3,max_length=20)
  email : str = Field(...,min_length=3,max_length=40)
  resume : UploadFile = Field(...)

class JobApplicationResumeUpdate(BaseModel):
   resume : UploadFile = Field(...)
  
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

@app.get('/api/job-boards/{id}/job-posts')
async def api_to_get_jobposts(id:int = 0):
  print('*****************',id,f'Type - {type(id)}******************************')
  with get_db_session() as session:
    # session.query(JobPost).filter() 
    jobPosts = session.query(JobPost).join(JobBoard).filter(JobBoard.id.__eq__(int(id))).all()
    print("\n************* Output is ************ ",jobPosts)
    return jobPosts
  
#*********************************************************************************
#Login Page
#*********************************************************************************
class AdminLoginForm(BaseModel):
   username : str
   password : str

@app.post("/api/admin-login")
async def admin_login(response: Response, admin_login_form: Annotated[AdminLoginForm, Form()]):
   auth_response = authenticate_admin(admin_login_form.username, admin_login_form.password)
   if auth_response is not None:
      secure = settings.PRODUCTION
      response.set_cookie(key="admin_session", value=auth_response, httponly=True, secure=secure, samesite="Lax")
      return {}
   else:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

@app.post("/api/admin-logout")
async def admin_login(request: Request, response: Response):
    delete_admin_session(request.cookies.get("admin_session"))
    print("Till Here I'm Good")
    secure = settings.PRODUCTION
    response.delete_cookie(key="admin_session",
                           httponly=True,
                           secure=secure,
                           samesite="Lax")
    return{}
   
@app.get("/api/me")
async def me(req: Request):
  return {"is_admin": req.state.is_admin}
#*********************************************************************************
#Job Boards
#*********************************************************************************
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

@app.get("/api/job_board")
async def get_job():
  try:
    with get_db_session() as session:
      job_board = session.query(JobBoard).all()
      return job_board
  except Exception as e:
    print("Failed to execute query ..!",e)
    raise server_exception("Internal Server Error")

@app.put("/api/job-boards/slug/{item_id}")
async def update_job_boards_logo(item_id:int ,payload: Annotated[JobBoardUpdateSlug , Form()]):
  try:
    #check weather its available in DB
    db = get_db_session()
    result = db.query(JobBoard).filter(JobBoard.id == item_id).first()
    if not result:
      return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content = ( {"Details":f"Job board with item_id {item_id} not present ..!"})
      )
    #Update Logo
    result.slug = payload.slug
    insert_to_db(result,db)
    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={
        "slug":payload.slug
      } 
    )
  except Exception as e:
    print(e)
    raise server_exception("Internal Server Error: Failed to update the job_board")
  finally:
    if db:
      db.close()
      print("Session closed ..!")

@app.put("/api/job-boards/logo/{item_id}")
async def update_job_boards_logo(item_id:int ,payload: Annotated[JobBoardUpdateLogo,Form()]):
  try:
    #check weather its available in DB
    db = get_db_session()
    result = db.query(JobBoard).filter(JobBoard.id == item_id).first()
    if not result:
      return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content = ( {"Details":f"Job Board with item_id {item_id} not present ..!"})
      )
    
    #Validate the extension
    extension = payload.logo.filename.split(".")[1] 
    validate_extensions( extension.lower(), ["png","jpg","jpeg","gif"])
    
    #Upload file
    upload_folder = os.path.join("static","images")
    os.makedirs(upload_folder,exist_ok=True)
    generated_name = f"logo_{secure_random_string()}.{extension}"
    file_path = os.path.join(upload_folder,generated_name)
    contents = await payload.logo.read()
    result_path = upload_file(settings.SUPABASE_BUCKET, file_path, contents, payload.logo.content_type)
    print(result_path)

    #Update Logo
    result.logo = result_path
    insert_to_db(result,db)
    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={
        "logo":result_path
      } 
    )
  except Exception as e:
    print(e)
    raise server_exception("Internal Server Error: Failed to update the job_board")
  finally:
    if db:
      db.close()
      print("Session closed ..!")

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
#*******************************************
#Job Applications
#*******************************************
@app.get("/api/job-application")
async def get_all_job_application():
  try:
    result = get_details(JobApplication)
    print("\n\n Data : ", result)
    return result
  except Exception as e:
    print("Failed to get applications : ",e)
    raise server_exception("Failed to get the details: Internal server error ..!")

@app.post("/api/job-application")
async def create_application(payload: Annotated[job_application , Form()],
                             background_tasks: BackgroundTasks,
                             vector_store = Depends(get_vector_store)):
  try:
    background_tasks.add_task(send_email,
    payload.email,
    "Acknowledgement",
    "We have received your job application"                          
    )
    #check if Job Post is CLOSED
    result = job_is_closed(payload.job_post_id)
    if result['status']:
      return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"Message":f"Job Post is closed ..!"}
      )

    #Validate the extension
    extension = payload.resume.filename.split(".")[1] 
    validate_extensions( extension.lower(), ['pdf','doc','docx','.odt'])
    
    #Upload the file
    resume_content = await payload.resume.read()
    upload_folder = os.path.join('static','resume')
    os.makedirs(upload_folder,exist_ok=True)
    first_name = payload.first_name
    resume_name = f"{first_name}_{secure_random_string()}.{extension}"
    save_path = os.path.join(upload_folder,resume_name)
    result_path = upload_file(settings.SUPABASE_BUCKET, save_path, resume_content, payload.resume.content_type)

    #Logg data to database
    data = JobApplication(job_post_id=payload.job_post_id,
                          first_name=payload.first_name,
                          last_name=payload.last_name,
                          email=payload.email,
                          resume=result_path)
    insert_to_db(data)
    print("\n\n Application is Added \n\n")
    background_tasks.add_task(ingest_resume_for_recommendataions, resume_content, 
                              result_path, data.id, vector_store)
    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={"Message":f"Application is submitted for job_post_id: {payload.job_post_id}"}
    )
  except Exception as e:
    print(e)
    raise server_exception("Failed to create job application : Internal server error")

@app.put("/api/job-application/resume-edit/{id}")
async def edit_application(id: int ,payload: Annotated[JobApplicationResumeUpdate, Form()]):
  try:
    #check weather is application availkable to edit
    db_session = get_db_session()
    result = db_session.query(JobApplication).filter(JobApplication.id == id).first()
    if not result:
      return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        conetent = {"error": f"Job Application with {id} not awailable"}
      )
    
    #check the extension
    extension = payload.resume.filename.split(".")[-1]
    print(extension)
    validate_extensions(extension.lower(),['pdf','doc','docx','odt'])
    content = await payload.resume.read()
    upload_folder = os.path.join("static","resume")
    random_string = secure_random_string()
    save_path = os.path.join(upload_folder,f"resume_{random_string}.{extension}")
    result_path = upload_file(settings.SUPABASE_BUCKET, save_path, content, payload.resume.content_type)
    print(result_path)
    result.resume = result_path 
    insert_to_db(result,db_session)

    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content = {"Message":"Resume is updated ..!"}
    )
  except Exception as e:
    raise server_exception("Failed to update the job application ..!",e)
  finally:
    if db_session:
      db_session.close()

@app.get("/api/job-posts/{job_post_id}/recommend")
async def api_recommend_resume(
   job_post_id, 
   vector_store = Depends(get_vector_store)):
   db = get_db_session()
   job_post = db.get(JobPost, job_post_id)
   if not job_post:
      raise HTTPException(status_code=400)
   job_description = job_post.description
   recommended_resume = get_recommendation(job_description, vector_store)   
   application_id = recommended_resume.metadata["_id"]
   job_application = db.get(JobApplication, application_id)
   return job_application

#*******************************************
#Job Posts
#*******************************************
class jobPost(BaseModel):
  title: str = Field(...,min_length = 3, max_length = 100)
  description: str = Field(...,min_length = 3)
  job_board_id: int = Field(...,ge=1,el=10)
  
@app.post("/api/job-posts")
async def create_new_job_post(job_post: Annotated[jobPost,Form()]):
  try:
    data = JobPost(title = job_post.title, job_board_id = job_post.job_board_id, description = job_post.description)
    insert_to_db(data)
  except IntegrityError as e:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"Message":"Job board is not exist please provide the correct job boards ..!"}
    )
  return JSONResponse(
    status_code = status.HTTP_200_OK,
    content = {"message":"New Job post is created ..!"}
  )

@app.post("/api/review-job-description")
async def review_job_post(job_post: Annotated[jobPost,Form()]):
  try:
    final_description = review_application(job_post.description)
  except Exception as e:
    print(e)
    return server_exception("Internal Server Error : Failed to review job")
  return JSONResponse(
    status_code = status.HTTP_200_OK,
    content = {"description":final_description.overall_summary,
    "revised_description":final_description.revised_description}
  )

@app.put("/api/job-posts/{job_post_id}/{job_status}")
async def update_job_post(job_post_id: int,job_status:str):
  try:
    db_session = get_db_session()
    #Check if job posts exists
    result = db_session.query(JobPost).filter(JobPost.id == job_post_id).first()
    if result:
      result.job_post_status = job_status
      insert_to_db(result)
    else:
      return JSONResponse(
        status_code= status.HTTP_400_BAD_REQUEST,
        content={"error" : "Job post not exist"}
      )
    return JSONResponse(
      status_code= status.HTTP_200_OK,
      content = {"Message":f"{status} updated in Job Post Status .."}
    )
  except Exception as e:
    print(e)
    raise server_exception("Failed to update job posts : Internal Server Error")

app.mount("/assets", StaticFiles(directory="frontend/build/client/assets"))
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
  indexFilePath = os.path.join("frontend", "build", "client", "index.html")
  return FileResponse(path=indexFilePath, media_type="text/html")

