import gradio as gr
import json
from prototype import chat
from prototype import get_ip
from uszipcode import SearchEngine
import pandas as pd
import os

global startingMsg
startingMsg = "Default Text"
#dynamic_text = gr.State(value="Initial text")
#def update_text(new_text):
#    dynamic_text = new_text
#    return new_text,
def setStartMsg(setMsg):
     global startingMsg
     startingMsg = setMsg
def getStartMsg():
     print(startingMsg)
     return startingMsg
def update_label(input_text):
    #Designed to work with gradio text objects if necessary
    return f"{input_text}"

def log_user_activity(ip_address, completion, file_name='user_log.xlsx'):
    # TODO: Transition from demo excel to Azure Data Table
    # Note that completion is here to distinguish between reaching end state or not
    # Check if the file exists to either read the existing data or create a new DataFrame
    if os.path.exists(file_name):
        df = pd.read_excel(file_name)
    else:
        df = pd.DataFrame(columns=['IP Address', 'Usage Count'])
    
    # Check if the user (IP address) exists in the DataFrame
    if ip_address in df['IP Address'].values:
        # If yes, and if user has reached end state, increment the usage count
        if completion:
            df.loc[df['IP Address'] == ip_address, 'Usage Count'] += 1
    else:
        # If not, add the new user with a usage count of 0 to show they have opened the tool
        new_row = {'IP Address': ip_address, 'Usage Count': 0}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Save the DataFrame to an Excel file
    with pd.ExcelWriter(file_name, engine='openpyxl', mode='w') as writer:
        df.to_excel(writer, index=False)

with open('labels-en.json', 'r') as labels:
    englishLabels = json.load(labels)

with open('labels-sp.json', 'r') as labels:
    spanishLabels = json.load(labels)

def findStateFromZipCode(zipCode):
    search = SearchEngine()
    stateName = search.by_zipcode(zipCode)
    if stateName is None:
        print("No state found for the given zipcode")
    else:
        return stateName.state_long

stateZipCode = 0
def buildInfoAboutUserFromQues1(zipCode, kidsBelow5, kidsAbove5Below18):
        global stateZipCode
        stateZipCode = zipCode
        promptInfo = "My zipcode is " + zipCode + ". I have " + kidsBelow5 + " kids under age 5 and " + kidsAbove5Below18 + " kids between the ages of 5 and 18. "
        return promptInfo

def buildInfoAboutUserFromQues2(enrolledSnap, enrolledWic):
        enrolledPrompt = ""
        if(enrolledSnap):
             enrolledPrompt += "I am already enrolled in SNAP. "
        if(enrolledWic):
             enrolledPrompt += "I am already enrolled in WIC. "
        promptInfo = enrolledPrompt
        return promptInfo

def build_info_about_user_from_ques3(household_size, household_above_60, us_citizen, job_or_self_emp_income, other_sources_income, college_studies, age_bucket, pregnancy_status, children_age_status):
    prompt_info = (
        f"My household size is {household_size} people. "
        f"Does my household include someone who is 60 or older, or someone who has a disability? {household_above_60}. "
        f"{'.'.join(us_citizen)}. "
        f"{job_or_self_emp_income} is my monthly household income before taxes from my job. "
        f"{other_sources_income} is my monthly household income from other sources. "
        f"Am I enrolled in college or vocational school half-time or more? {college_studies}. "
        f"{'.'.join(age_bucket)}. "
        f"Are any of the members of my household pregnant, or were pregnant in the last 6 months? {pregnancy_status}. "
        f"Are any members of my household a child under age 5? {children_age_status}. "
    )
    return prompt_info


def nextQuestionnaire2(isEnrolledForSnap, isEnrolledForWic, promptInfo):
        enrolledSnap = isEnrolledForSnap
        enrolledWic = isEnrolledForWic
        questionnairePage3 = gr.update(visible=True)
        questionnairePage2 = gr.update(visible=False)
        promptInfo += buildInfoAboutUserFromQues2(enrolledSnap, enrolledWic)
        #print(promptInfo)
        return questionnairePage3, questionnairePage2, promptInfo

def nextQuestionnaire1(ques1Input, ques2Input, ques3Input, promptInfo):
        zipCode = ques1Input
        kidsBelow5 = ques2Input
        kidsAbove5Below18 = ques3Input
        # prompt = ques1 + " " + ques2 + " " + ques3
        # print(prompt)
        introQuestionnaire = gr.update(visible=False)
        questionnairePage2 = gr.update(visible=True)
        promptInfo += buildInfoAboutUserFromQues1(zipCode, kidsBelow5, kidsAbove5Below18)
        #print(promptInfo)
        return introQuestionnaire, questionnairePage2, zipCode, kidsBelow5, kidsAbove5Below18, promptInfo

def start():
        #Runs when user first enters the survey (one click from starting page)
        introQuestionnaire = gr.update(visible=True)
        introPage = gr.update(visible=False)
        ip_address = get_ip()
        log_user_activity(ip_address, False)
        return introQuestionnaire, introPage

def startbot(ques1, ques2, ques3, ques4, ques5, ques6, ques7, ques8, ques9, promptInfo):
        householdSize = ques1
        housholdAbove60 = ques2
        usCitizen = ques3
        jobOrSelfEmpIncome = ques4
        otherSourcesIncome = ques5
        collegeStudies = ques6
        ageBucket = ques7
        pregnancyStatus = ques8
        childrenAgeStatus = ques9
        promptInfo += buildInfoAboutUserFromQues3(ques1, ques2, ques3, ques4, ques5, ques6, ques7, ques8, ques9)
        botScreen = gr.update(visible=True)
        questionnairePage3 = gr.update(visible=False)
        emptyStr, initialBotAnswer = chatInvoke("What programs am I eligible for?", promptInfo, [])
        print("Initial bot answer:")
        print(initialBotAnswer)
        print()
        #Vestigal tactics that if expanded on further could lead to other formats for chatbot messaging first:
        #chatbot.append(initialBotAnswer[1], is_user=False)
        #gr.Markdown("")
        #gr.Markdown(initialBotAnswer[-1][1])
        #gr.Markdown("")
        startString = initialBotAnswer[-1][1] + "\nPlease use the below chatbot to ask the AI helper any additional questions"
        setStartMsg(startString)
        global label
        label.value = getStartMsg()
        #This is what we have chosen to define as end state
        ip_address = get_ip()
        log_user_activity(ip_address, True)
        return botScreen, questionnairePage3, householdSize, housholdAbove60, usCitizen, jobOrSelfEmpIncome, otherSourcesIncome, collegeStudies, ageBucket, pregnancyStatus, childrenAgeStatus, promptInfo, startString

def chatInvoke(msg, promptInfo, chat_history):
        global stateZipCode
        stateFromZip = findStateFromZipCode(stateZipCode)
        userMsg = msg
        #Through testing, giving the bot what is effectively a transcript appears to work best, although not as elegant as something like a summary
        context = ". Bear in mind we have already had the following exchange which may have relevant information: "
        for chatTuple in chat_history:
             context += ("You: " + chatTuple[0])
             context += ("Me: " + chatTuple[1])
        prompt = "Given the following information about me: " + "I am from the state " + stateFromZip +  ". " + promptInfo + " " + msg + context
        print("Prompt:")
        print(prompt)
        response = chat(prompt, stateFromZip)
        #Elegant as the context will not be repeated needlessly throughout chat_history
        chat_history.append((userMsg, response))
        #print(stateFromZip)
        #print(prompt)
        #print(response)
        #print(chat_history)
        return "", chat_history

with gr.Blocks(css=".label-class { font-size: 14px; } .label-text { display: none; }") as demo:

    #states for questionnaire 1
    zipCode = gr.State(value="")
    kidsAbove5Below18 = gr.State(value="")
    kidsBelow5 = gr.State(value="")

    #states for questionnaire 2
    enrolled = gr.State(value="")

    #states for questionnaire 3
    householdSize = gr.State(value="")
    housholdAbove60 = gr.State(value="")
    usCitizen = gr.State(value="")
    jobOrSelfEmpIncome = gr.State(value="")
    otherSourcesIncome = gr.State(value="")
    collegeStudies = gr.State(value="")
    ageBucket = gr.State(value="")
    pregnancyStatus = gr.State(value="")
    childrenAgeStatus = gr.State(value="")
    promptInfo = gr.State(value="")
    response = gr.State(value="")
    state = gr.State(value="")

    with gr.Group(visible=False) as botScreen:
        with gr.Blocks() as sosChatBot:
            with gr.Column():
                global label
                label = gr.Label(label="The basic answer:", value="Initial text")
                chatbot = gr.Chatbot(bubble_full_width = False)

                #Below are vestigal components to do with Markdowns and live updates of components, I have left them here because they represent good ways to test functionality

                #gr.Markdown("")
                #gr.Markdown("")
                #markdown_component = gr.Markdown(dynamic_text.value)
                #markdown_display = gr.Markdown()
                #update_button = gr.Button("Update Text")
                #new_text_input = gr.Textbox(label="Enter new text")
                #update_button.click(fn=update_text, inputs=new_text_input, outputs=dynamic_text)
                #dynamic_text.change(fn=lambda x: x, inputs=dynamic_text, outputs=markdown_display)

                #input_text = gr.Textbox(label="Enter text to update label")
                #button = gr.Button("Update Label")
                #button.click(fn=update_label, inputs=input_text, outputs=label)

                msg = gr.Textbox(label="Enter questions here:")
                msg.submit(chatInvoke, [msg, promptInfo, chatbot], [msg, chatbot])
                with gr.Row():
                    clear = gr.ClearButton([msg, chatbot])
                    submit = gr.Button("Submit", variant="primary")
                    submit.click(chatInvoke, [msg, promptInfo, chatbot], [msg, chatbot])

    with gr.Group(visible=False) as questionnairePage3:
        with gr.Tab(englishLabels['lang-1']):
            gr.Markdown("# <p style='text-align: center;'>{}</p>".format("Our AI Helper can save you time!"))
            gr.Markdown("<p style='text-align: center;'>{}</p>".format("Here are the 9 questions we need you to answer so the AI Helper knows what programs you qualify for, then it will find links or phone numbers to help you apply. Make sure you have a good internet connection, and your phone battery is charged or plugged in."))
            gr.Markdown("<p style='text-align: center;'>{}</p>".format("All of your answers are private to you, and will not be shared with anybody."))
            ques1 = gr.Textbox(label="1. Household size", info="Your household is the people you live with and buy food with. You must include children 21 or younger, parents and spouses if you are living together. ")
            ques2 = gr.Radio(["Yes", "No"], label="2. Does your household include someone who is 60 or older, or someone who has a disability?")
            ques3 = gr.CheckboxGroup(["I'm a US citizen", "I've been a Legal Permanent Resident for 5 or more years", "I'm a refugee or asylee", "I have a child that has one of the above statuses"], label="3. Do any of these apply to you?")
            ques4 = gr.Textbox(label="4. Monthly household income before taxes from jobs or self-employment")
            ques5 = gr.Textbox(label="5. Monthly household income from other sources", info="This includes Social Security disability, Child Support, Worker's Comp, Unemployment, Pension Income, or other sources of income.")
            ques6 = gr.Radio(["Yes", "No"], label="6. Are you enrolled in a college or vocational school half-time or more?")
            ques7 = gr.CheckboxGroup(["I'm 17 or younger", "I'm 50 or older", "I'm receiving TANF (cash assistance) or disability payments", "I have parental control of a child under age 12", "I'm in a job training program", "I'm being paid to work an average of 20 hours per week", "I'm approved for work study and anticipate working during the term", "I'm unable to work as determined by a health professional"], label="7. If yes, which of the following apply to you?")
            ques8 = gr.Radio(["Yes", "No"], label="8. Are any of the members of your household pregnant, or was pregnant in the last 6 months?")
            ques9 = gr.Radio(["Yes", "No"], label="9. Are any of the members of your household an infant or child up that hasn't yet had their 5th birthday?")
            aiHelper = gr.Button("Send to AI Helper (takes 10 seconds)")
            aiHelper.click(startbot, inputs=[ques1,ques2,ques3,ques4,ques5,ques6,ques7,ques8,ques9, promptInfo], outputs=[botScreen,questionnairePage3,householdSize,housholdAbove60,usCitizen,jobOrSelfEmpIncome,otherSourcesIncome,collegeStudies,ageBucket,pregnancyStatus,childrenAgeStatus,promptInfo, label])
            #Previously used this click to update first message, but is no longer needed, kept here to do anything else "on activation" of AI
            #aiHelper.click(fn=getStartMsg, inputs=None, outputs=label)
        with gr.Tab(englishLabels['lang-2']):
            gr.Markdown("# <p style='text-align: center;'>{}</p>".format("¡Nuestro ayudante de IA puede ahorrarle tiempo!"))
            gr.Markdown("<p style='text-align: center;'>{}</p>".format("Estas son las 9 preguntas que necesitamos que respondas para que el Ayudante de IA sepa para qué programas calificas, luego encontrará enlaces o números de teléfono para ayudarte a postularte. Asegúrate de tener una buena conexión a Internet y de que la batería de tu teléfono esté cargada o enchufada."))
            gr.Markdown("<p style='text-align: center;'>{}</p>".format("Todas sus respuestas son privadas para usted y no se compartirán con nadie."))
            ques1 = gr.Textbox(label="1. Cuántas personas viven en el hogar", info="Su hogar son las personas con las que vive y con las que compra alimentos. Debe incluir a los niños de 21 años o menos, padres y cónyuges si viven juntos. ")
            ques2 = gr.Radio(["Sí", "No"], label="2. ¿Su hogar incluye a alguien que tiene 60 años o más, o alguien que tiene una discapacidad?")
            ques3 = gr.CheckboxGroup(["No soy ciudadano de Estados Unidos", "He sido residente legal permanente durante 5 años o más", "I'm a refugee or asylee", "Tengo un hijo que tiene uno de los estados anteriores"], label="¿Alguno de estos casos se aplican a tí?")
            ques4 = gr.Textbox(label="4. Ingresos mensuales del hogar antes de impuestos por trabajo o trabajo por cuenta propia")
            ques5 = gr.Textbox(label="5. Ingresos mensuales del hogar de otras fuentes", info="Esto incluye discapacidad del Seguro Social, manutención de los hijos, compensación laboral, desempleo, ingresos de pensiones u otras fuentes de ingresos.")
            ques6 = gr.Radio(["Sí", "No"], label="6. ¿Está inscrito en una universidad o escuela vocacional a medio tiempo o más?")
            ques7 = gr.CheckboxGroup(["Tengo 17 años o menos", "Tengo 50 años o más", "Estoy recibiendo TANF (asistencia en efectivo) o pagos por discapacidad", "Tengo el control parental de un niño menor de 12 años", "Estoy en un programa de capacitación laboral", "Me pagan por trabajar una media de 20 horas semanales", "Estoy aprobado para el estudio de trabajo y preveo trabajar durante el plazo", "No puedo trabajar según lo determine un profesional de la salud"], label="7. ¿Cuál de las siguientes opciones se aplica a usted?")
            ques8 = gr.Radio(["Sí", "No"], label="8. ¿Alguno de los miembros de su hogar está embarazada o estuvo embarazada en los últimos 6 meses?")
            ques9 = gr.Radio(["Sí", "No"], label="9. ¿Alguno de los miembros de su hogar es un bebé o niño que aún no ha cumplido 5 años?")
            aiHelper = gr.Button("Enviar al ayudante de IA (esperas 10 segundos)")
            aiHelper.click(startbot, inputs=[ques1,ques2,ques3,ques4,ques5,ques6,ques7,ques8,ques9, promptInfo], outputs=[botScreen,questionnairePage3,householdSize,housholdAbove60,usCitizen,jobOrSelfEmpIncome,otherSourcesIncome,collegeStudies,ageBucket,pregnancyStatus,childrenAgeStatus,promptInfo])
            #aiHelper.click(fn=getStartMsg, inputs=None, outputs=label)

    with gr.Group(visible=False) as questionnairePage2:
        logo=gr.Image("images/NoHungry.svg", height=40, width=100, interactive=False, show_label=False, show_download_button=False)
        introPic=gr.Image("images/basic-program-list.jpg", interactive=False, show_label=False, show_download_button=False)
        with gr.Tab(englishLabels['lang-1']):
            gr.Markdown("# <p style='text-align: center;'>{}</p>".format("We found 2 programs in your area that you may be eligible for:"))
            gr.Markdown("<p style='text-align: left;'>{}</p>".format("You may be eligible for Basic Food (SNAP)."))
            isEnrolledForSnap = gr.Checkbox(label="I'm already enrolled", value=False)
            gr.Markdown("<p style='text-align: left;'>{}</p>".format("You may be eligible for the Nutrition Program for Women, Infants and Children (WIC)."))
            isEnrolledForWic = gr.Checkbox(label="I'm already enrolled", value=False)
            gr.Markdown("# <p style='text-align: left;'>{}</p>".format("How to apply "))
            gr.Markdown("<p style='text-align: left;'>{}</p>".format("While each program has a unique application process, our questionnaire (9 questions) can tell you which programs you qualify for, and give you the links or phone number."))
            gr.Markdown("<p style='text-align: left;'>{}</p>".format("All of your answers are private to you, and will not be shared with anybody."))
            questionnairePage2Button = gr.Button("Start questionnaire", variant="primary")
            gr.Markdown("<a style='text-align: center;font-weight:400' href='https://foodfinder.us'>{}</a>".format(englishLabels['intro-footer-title']+ englishLabels['intro-footer-content']))
            questionnairePage2Button.click(nextQuestionnaire2, inputs=[isEnrolledForSnap, isEnrolledForWic, promptInfo], outputs=[questionnairePage3,questionnairePage2, promptInfo])
        with gr.Tab(englishLabels['lang-2']):
            gr.Markdown("# <p style='text-align: center;'>{}</p>".format("Encontramos programas en su área para los que puede ser elegible:"))
            gr.Markdown("<p style='text-align: left;'>{}</p>".format("Puede ser elegible para alimentos básicos (SNAP)."))
            isEnrolledForSnap = gr.Checkbox(label="Ya estoy inscrita.", value=False)
            gr.Markdown("<p style='text-align: left;'>{}</p>".format("Puede ser elegible para el Programa de Nutrición para Mujeres, Bebés y Niños (WIC)."))
            isEnrolledForWic = gr.Checkbox(label="Ya estoy inscrita.", value=False)

            gr.Markdown("# <p style='text-align: left;'>{}</p>".format("Cómo presentar la solicitud "))
            gr.Markdown("<p style='text-align: left;'>{}</p>".format("Si bien cada programa tiene un proceso de solicitud único, nuestro cuestionario (9 preguntas) puede decirle para qué programas califica y luego darle los enlaces o el número de teléfono"))
            gr.Markdown("<p style='text-align: left;'>{}</p>".format("Todas sus respuestas son privadas para usted y no se compartirán con nadie."))
            questionnairePage2Button = gr.Button("Empezar cuestionario", variant="primary")
            gr.Markdown("<a style='text-align: center;font-weight:400' href='https://foodfinder.us'>{}</a>".format(spanishLabels['intro-footer-title']+ spanishLabels['intro-footer-content']))
            questionnairePage2Button.click(nextQuestionnaire2, inputs=[isEnrolledForSnap, isEnrolledForWic, promptInfo], outputs=[questionnairePage3,questionnairePage2, promptInfo])

    with gr.Group(visible=False) as introQuestionnaire:
        logo=gr.Image("images/NoHungry.svg", height=40, width=100, interactive=False, show_label=False, show_download_button=False)
        introPic=gr.Image("images/basic-form.jpg", interactive=False, show_label=False, show_download_button=False)
        with gr.Tab(englishLabels['lang-1']):
            gr.Markdown("# <p style='text-align: center;'>{}</p>".format("Your location and family details"))
            gr.Markdown("<p style='text-align: center;'>{}</p>".format("These 3 questions help determine program eligibility."))
            gr.Markdown("<p style='text-align: center;'>{}</p>".format("All of your answers are private to you, and will not be shared with anybody."))
            ques1 = gr.Textbox(label="1. What is your location's ZIP code?", info="We're asking where you live so we can help you find all the benefits available in your area")
            ques2 = gr.Textbox(label="2. How many kids do you have below age 5?", info="More programs may be available depending on your answer")
            ques3 = gr.Textbox(label="3. How many kids do you have aged 5-18?", info="More programs may be available depending on your answer.")
            nextButton = gr.Button("Show nearby programs", variant="primary")
            nextButton.click(nextQuestionnaire1, inputs = [ques1, ques2, ques3, promptInfo],outputs=[introQuestionnaire, questionnairePage2,zipCode,kidsBelow5,kidsAbove5Below18,promptInfo] )

        with gr.Tab(englishLabels['lang-2']):
            gr.Markdown("# <p style='text-align: center;'>{}</p>".format("Tu ubicación y datos familiares"))
            gr.Markdown("<p style='text-align: center;'>{}</p>".format("Estas 3 preguntas ayudan a determinar la elegibilidad para el programa."))
            gr.Markdown("<p style='text-align: center;'>{}</p>".format("Todas sus respuestas son privadas para usted y no se compartirán con nadie."))
            ques1 = gr.Textbox(label="1. ¿Cuál es el código POSTAL de tu ubicación?", info="Te preguntamos dónde vives para ayudarte a encontrar todas las ventajas disponibles en tu zona.")
            ques2 = gr.Textbox(label="2. ¿Cuántos hijos tiene por debajo de los 5 años?", info="Es posible que haya más programas disponibles dependiendo de su respuesta")
            ques3 = gr.Textbox(label="3. ¿Cuántos hijos tiene de 5 a 18 años?", info="Es posible que haya más programas disponibles dependiendo de su respuesta.")
            nextButton = gr.Button("Mostrar programas cercanos", variant="primary")
            nextButton.click(nextQuestionnaire1, inputs = [ques1, ques2, ques3, promptInfo],outputs=[introQuestionnaire, questionnairePage2,zipCode,kidsBelow5,kidsAbove5Below18,promptInfo] )
    with gr.Group(visible=True) as introPage:
      
        logo=gr.Image("images/NoHungry.svg", height=40, width=100, interactive=False, show_label=False, show_download_button=False)
        introPic=gr.Image("images/intro-page.jpg", interactive=False, show_label=False, show_download_button=False)

        with gr.Tab(englishLabels['lang-1']):

            gr.Markdown("# <p style='text-align: center;'>{}</p>".format(englishLabels['intro-title']))
            gr.Markdown("<p style='text-align: center;'>{}</p>".format(englishLabels['intro-desc-1']))
            gr.Markdown("<p style='text-align: center;weight:400;font-size:14px;font:Gotham;'>{}</p>".format(englishLabels['intro-desc-2']))
            getStarted = gr.Button(englishLabels['get-started'], variant="primary")
            getStarted.click(start,[],[introQuestionnaire,introPage])
            gr.Markdown("<a style='text-align: center;font-weight:400' href='https://foodfinder.us'>{}</a>".format(englishLabels['intro-footer-title']+ englishLabels['intro-footer-content']))

        with gr.Tab(englishLabels['lang-2']):

            gr.Markdown("# <p style='text-align: center;'>{}</p>".format(spanishLabels['intro-title']))
            gr.Markdown("<p style='text-align: center;'>{}</p>".format(spanishLabels['intro-desc-1']))
            gr.Markdown("<p style='text-align: center;weight:400;font-size:14px;font:Gotham;'>{}</p>".format(spanishLabels['intro-desc-2']))
            getStarted = gr.Button(spanishLabels['get-started'], variant="primary")
            getStarted.click(start,[],[introQuestionnaire,introPage])
            gr.Markdown("<a style='text-align: center;font-weight:400' href='https://foodfinder.us'>{}</a>".format(spanishLabels['intro-footer-title']+ spanishLabels['intro-footer-content']))

demo.launch()
