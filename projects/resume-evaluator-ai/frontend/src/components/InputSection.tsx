// SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useState } from 'react';
import pdfToText from 'react-pdftotext';
import TextareaAutosize from '@mui/material/TextareaAutosize';
import './InputSection.css';
import axios from 'axios';

interface InputSectionProps {
  setCandidateData: React.Dispatch<React.SetStateAction<CandidateData[]>>;
  setGlobalJobDescription?: React.Dispatch<React.SetStateAction<string>>;
}

export interface CandidateData {
  score: string;
  name: string;
  justification: string;
  resumeSummary: string;
}

interface AnalyseRequest {
  companyName: string;
  roleName: string;
  jobDescription: string;
  resumeText: string;
}

interface AnalyseResponse {
  message: string;
  data: CandidateData;
}

const InputSection: React.FC<InputSectionProps> = ({
  setCandidateData,
  setGlobalJobDescription,
}) => {
  const [files, setFiles] = useState<FileList | null>(null);
  const [resumeTexts, setResumeTexts] = useState<string[]>([]);
  const [companyName, setCompanyName] = useState<string>('');
  const [roleName, setRoleName] = useState<string>('');
  const [jobDescription, setJobDescription] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    if (files?.length ?? 0 > resumeTexts.length) {
      extractText();
    }
  }, [files]);

  useEffect(() => {
    if (isSubmitting && resumeTexts.length === files?.length) {
      getScores();
      setIsSubmitting(false);
    }
  }, [isSubmitting, resumeTexts]);

  async function extractText() {
    try {
      console.log('calling extractText');
      console.log('files:', files);
      if (files && files.length > 0) {
        for (let i = 0; i < files.length; i++) {
          const file = files[i];
          const text = await pdfToText(file);
          setResumeTexts((prev) => [...prev, text]);
        }
      }
    } catch (error) {
      console.error('Failed to extract text from pdf');
    }
  }

  async function getScores() {
    try {
      // console.log('calling getScores');
      // console.log('companyName:', companyName);
      // console.log('roleName:', roleName);
      // console.log('jobDescription:', jobDescription);
      // console.log('resumeTexts:', resumeTexts);

      for (let i = 0; i < resumeTexts.length; i++) {
        const resumeText = resumeTexts[i];
        // console.log('candidate number:', i + 1);
        // console.log('resumeText:', resumeText);
        const requestData: AnalyseRequest = {
          companyName: companyName,
          roleName: roleName,
          jobDescription: jobDescription,
          resumeText: resumeText,
        };

        const response = await axios.post<AnalyseResponse>(
          'http://localhost:3001/llm-chat/generate-score',
          requestData
        );
        if (response.status === 200) {
          console.log('Successfully called API!');
          console.log('API response:', response.data.data);
          setCandidateData((prevData) => [...prevData, response.data.data]);
        } else {
          alert('Unable to call API.');
        }
      }
    } catch (error) {
      alert('An error occurred!');
    }
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const form = event.target as HTMLFormElement;
    const inputFiles = form.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;
    if (!inputFiles.files) return;
    const inputCompanyName = form.querySelector(
      'input[name="companyName"]'
    ) as HTMLInputElement;
    const inputRoleName = form.querySelector(
      'input[name="roleName"]'
    ) as HTMLInputElement;
    const inputJobDescription = form.querySelector(
      'textarea[name="jobDescription"]'
    ) as HTMLTextAreaElement;

    // console.log(inputCompanyName.value);
    // console.log(inputRoleName.value);
    // console.log(inputJobDescription.value);
    setFiles(inputFiles.files);
    setCompanyName(inputCompanyName.value);
    setRoleName(inputRoleName.value);
    setJobDescription(inputJobDescription.value);
    if (setGlobalJobDescription) {
      setGlobalJobDescription(inputJobDescription.value);
    }

    setIsSubmitting(true);
  };

  return (
    <div>
      <h1 className="title">Input Section</h1>
      <form onSubmit={handleSubmit} className="inputForm">
        <label className="inputLabel">Upload PDFs:</label>
        <input
          className="inputFieldFile"
          type="file"
          accept="application/pdf"
          multiple
        />
        <label className="inputLabel">Company name:</label>
        <input className="inputFieldShort" type="text" name="companyName" />
        <label className="inputLabel">Role name:</label>
        <input className="inputFieldShort" type="text" name="roleName" />
        <label className="inputLabel">Job description:</label>
        <TextareaAutosize className="inputFieldLong" name="jobDescription" />
        <button className="submitButton" type="submit">
          Submit
        </button>
      </form>
    </div>
  );
};

export default InputSection;
