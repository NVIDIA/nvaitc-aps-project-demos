// SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

const OpenAI = require('openai');
require("dotenv").config();

const openai = new OpenAI({
  apiKey: process.env.NVIDIA_API_KEY,
  baseURL: 'https://integrate.api.nvidia.com/v1',
});

const sample_prompt = "Given the job description below, please score the resume for the role of Software Engineer at Google and identify their name.\n\nHere is a job description of the role that you can use to score the candidate. \nJob Description:\nWe are looking for a Software Engineer to join our team. You will work with our engineers to develop high-quality software. You will also work on various projects to improve our software. You should have experience in software development and be familiar with programming languages such as Java, C++, and Python.\n\nResume:\nI am Jason, a software engineer with 5 years of experience. I have worked on various projects to develop high-quality software. I am familiar with programming languages such as Java, C++, and Python. I have a Bachelor's degree in Computer Science from Stanford University.";
const sample_response = "Score: 8; Name: Jason; Justification: The resume is well-written and provides a clear overview of the candidate's experience and qualifications. The candidate has 5 years of experience as a software engineer and is familiar with programming languages such as Java, C++, and Python. The resume also mentions the candidate's Bachelor's degree in Computer Science from Stanford University. Overall, the resume is strong and demonstrates the candidate's qualifications for the role of Software Engineer at Google.; Resume Summary: The candidate is a software engineer with 5 years of experience and a Bachelor's degree in Computer Science from Stanford University. The candidate is familiar with programming languages such as Java, C++, and Python. The resume provides a clear overview of the candidate's experience and qualifications.";
// const sample_prompt_two = "Given the job description below, please score the resume for the role of Data Analyst at Facebook.\n\nHere is a job description of the role that you can use to score the candidate. \nJob Description:\nWe are looking for a Data Analyst to join our team. You will work with our data scientists to analyze data and provide insights. You will also work on various projects to improve our data analysis. You should have experience in data analysis and be familiar with data analysis tools such as SQL and Python.\n\nResume:\nI am George, a data analyst with 3 years of experience. I have worked on various projects to analyze data and provide insights. I am familiar with data analysis tools such as SQL and Python. I have a Bachelor's degree in Statistics from Harvard University.";
// const sample_response_two = "//Score: 7; //Name: George; //Justification: The resume is well-written and provides a clear overview of the candidate's experience and qualifications. The candidate has 3 years of experience as a data analyst and is familiar with data analysis tools such as SQL and Python. The resume also mentions the candidate's Bachelor's degree in Statistics from Harvard University. Overall, the resume is strong and demonstrates the candidate's qualifications for the role of Data Analyst at Facebook.; //Summary: The candidate is a data analyst with 3 years of experience and a Bachelor's degree in Statistics from Harvard University. The candidate is familiar with data analysis tools such as SQL and Python. The resume provides a clear overview of the candidate's experience and qualifications.";
const llm_instructions = "You are a hiring manager assessing candidates for their suitabilities for a specific role, based on the job description and the candidate resumes. You are to assign each of them a score within the range 1 to 10. Identify the name of the candidate from the resume. You are to provide a short justification for the score and a short summary of the resume."

// Function to extract sections based on headers
function extractSections(text) {
    const scoreRegex = /Score:\s*(\d+)/;
    const nameRegex = /Name:\s*(\w+)/;
    const justificationRegex = /Justification:\s*([\s\S]*?)Resume Summary:/;
    const summaryRegex = /Resume Summary:\s*([\s\S]*)/;

    const scoreMatch = text.match(scoreRegex);
    const nameMatch = text.match(nameRegex);
    const justificationMatch = text.match(justificationRegex);
    const summaryMatch = text.match(summaryRegex);

    const score = scoreMatch ? scoreMatch[1].trim() : null;
    const name = nameMatch ? nameMatch[1].trim() : null;
    const justification = justificationMatch ? justificationMatch[1].trim() : null;
    const resumeSummary = summaryMatch ? summaryMatch[1].trim() : null;

    return { score, name, justification, resumeSummary };
}

async function generateScore(req, res) {
    try {
        console.log('generateScore in backend reached');
        const { companyName, roleName, jobDescription, resumeText } = req.body;

        const prompt = "Given the job description below, please score, on a scale of 1 - 10 where 10 is the best, and 1 is slightly suitable, the resume for the role of " + roleName + " at " + companyName + ".\n\nHere is a job description of the role that you can use to score the candidate and don't give high scores too easily. \nJob Description:\n" + jobDescription + "\n\nResume:\n" + resumeText;
        console.log('prompt generated');
        const completion = await openai.chat.completions.create({
            model: "meta/llama-3.1-405b-instruct",
            messages: [
                {
                  "role": "system",
                  "content": llm_instructions
                },
                {
                    "role": "user",
                    "content": sample_prompt
                },
                {
                    "role": "assistant",
                    "content": sample_response
                },
                {
                  "role": "user",
                  "content": prompt
                }
              ],
            temperature: 0.2,
            top_p: 0.7,
            max_tokens: 1024,
            stream: true
        });

        let result = '';
        for await (const chunk of completion) {
            result += chunk.choices[0]?.delta?.content || '';
        }
        console.log('result generated', result);

        const { score, name, justification, resumeSummary } = extractSections(result);

        // Output the extracted values
        // console.log("Score:", score);
        // console.log("Name:", name);
        // console.log("Justification:", justification);
        // console.log("Resume Summary:", resumeSummary);
        return res.status(200).json({ message: "Score generated", data: {score:score, name:name, justification:justification, resumeSummary: resumeSummary} });
    } catch (error) {
        console.log(error);
        return res.status(500).json({ message: "Error occurred", error: error });
    }
}

async function generateSuggestion(req, res) {
    try {
        console.log('generateSuggestion in backend reached');
        const { score, resumeSummary, jobDescription } = req.body;

        const prompt = "Given the score of " + score + " for a candidate whose resume summary is as follows:\n" + resumeSummary + "\n\nPlease provide a few suggestions on what the candidate can work on to improve their suitability for the role based on the job description below. Keep the response short.\n\nJob Description:\n" + jobDescription; 
        console.log('prompt generated');
        const completion = await openai.chat.completions.create({
            model: "meta/llama-3.1-405b-instruct",
            messages: [
                {
                  "role": "user",
                  "content": prompt
                }
              ],
            temperature: 0.2,
            top_p: 0.7,
            max_tokens: 1024,
            stream: true
        });

        let result = '';
        for await (const chunk of completion) {
            result += chunk.choices[0]?.delta?.content || '';
        }
        console.log('result generated', result);

        // Output the extracted values
        // console.log("Score:", score);
        // console.log("Name:", name);
        // console.log("Justification:", justification);
        // console.log("Resume Summary:", resumeSummary);
        return res.status(200).json({ message: "Score generated", data: result});
    } catch (error) {
        console.log(error);
        return res.status(500).json({ message: "Error occurred", error: error });
    }
}

module.exports = { generateScore, generateSuggestion };