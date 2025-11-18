from fastapi import FastAPI,HTTPException,Response
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health():
  return {"status": "ok"}

@app.get("/")
async def health():
  return {"message": "Hello World"}

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

#Query Parameters
@app.get("/job-boards")
async def job_boards(name:str = ""):
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
      
    if name == "bcg":
      for job in bcg_title:
        result.append({"title":job})
      
    if name == "atlas":
      for item in atlas:
        result.append({
          "title" : item["title"],
          "description": item["description"]
        })
    
    return JSONResponse(
      status_code= 200,
      content= result
    )
  except Exception as e:
    print("Error while processing the request",e)
    raise HTTPException(
      status_code=500,
      detail = f"Not able to process the request at the moment"
    )
  
  return {"title":""}

#Path Parameters
@app.get("/job-boards/{name}")
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
    if name in jd.keys():
      return jd[name]
    else:
      response.status_code = 404
      return {"error": "Not Found - Resource not available."}
      
  except Exception as e:
    print("Error while processing the request",e)
    raise HTTPException(
      status_code=500,
      detail = f"Not able to process the request at the moment"
    )
  return {"title":""}