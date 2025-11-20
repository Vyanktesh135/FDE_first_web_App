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
from fastapi.responses import RedirectResponse
import re

app = FastAPI()
class server_exception(Exception):
  def __init__(self,name):
    self.name = name

#Mounting Static Assets
app.mount("/static",StaticFiles(directory="static"),name = "static")
templates = Jinja2Templates(directory="templates")

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

@app.get("/health")
async def health():
  return {"status": "ok"}

@app.get("/", response_class = HTMLResponse,name="home")
async def home(request: Request):
  return templates.TemplateResponse("index.html",{"request":request})

@app.get("/render_test")
async def render_test():
  return {"message" : "test completed"}

@app.get("/add/")
async def addition(a:int =0 ,b:int = 0):
  print(a," + " , b)
  return {"result" : a+b}

@app.get("/multiply")
async def multiply(a:int = 0, b:int = 0):
  print(a," * ",b)
  return {"result" : a*b}

@app.get("/job-boards/upload",response_class=HTMLResponse,name="get_logo")
async def upload(request: Request):
  return templates.TemplateResponse("update_logo.html",{"request":request})

@app.post("/job-boards/update_logo",response_class = HTMLResponse,name="update_logo")
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
@app.get("/job-boards")
async def job_boards(name:str,title:str,request: Request):
  try:
    print("Name of Company",name)
    acme_title = ["Customer Support Executive","Project Manager"]  
    bcg_title = ["Technical Architect","Junior Software Developer"]
    atlas = [
      # {"title": "Customer Support Executive"},
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
    result = []
    if name == "acme":
      for job in acme_title:
        result.append({"title":job})
      
    elif name == "bcg":
      for job in bcg_title:
        result.append({"title":job})
      
    elif name == "atlas":
      for item in atlas:
        result.append({
          "title" : item["title"],
          "description": item["description"]
        })
    else:
      result.append({
        "title":"No title to display please provide correct name"
      })
    
    return templates.TemplateResponse(
      "job_boards.html",
      {
        "request":request,
        "details": result,
        "company": name,
        "src_title":title,
      }
    )
  
  except Exception as e:
    print("Error while processing the request",e)
    raise HTTPException(
      status_code=500,
      detail = f"Not able to process the request at the moment"
    )
  
  return {"title":""}

#Path Parameters
@app.get("/api/job-boards/{name}")
async def job_boards(name:str,response:Response ):
  try:
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