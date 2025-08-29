// SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ScatterPlot, { ScoreData } from './Scatterplot';
import { CandidateData } from './InputSection';
import { Button } from '@mui/material';
import axios from 'axios';
import './OutputSection.css';

const sampleData: CandidateData[] = [];
// const sampleData: CandidateData[] = [
//   {
//     score: '8',
//     name: 'Alice',
//     justification: 'Score explanation for Alice',
//     resumeSummary: "Summary of Alice's resume",
//   },
//   {
//     score: '6',
//     name: 'Bob',
//     justification: 'Score explanation for Bob',
//     resumeSummary: "Summary of Bob's resume",
//   },
//   {
//     score: '6',
//     name: 'Charlie',
//     justification: 'Score explanation for Charlie',
//     resumeSummary: "Summary of Charlie's resume",
//   },
//   {
//     score: '5',
//     name: 'Diana',
//     justification: 'Score explanation for Diana',
//     resumeSummary: "Summary of Diana's resume",
//   },
// ];

function extractScores(data: CandidateData[]): ScoreData[] {
  return data.map((item) => ({
    name: item.name,
    score: parseInt(item.score),
  }));
}

interface OutputSectionProps {
  data: CandidateData[];
  jobDescription: string;
}
const OutputSection: React.FC<OutputSectionProps> = ({
  data,
  jobDescription,
}) => {
  const [suggestions, setSuggestions] = React.useState<string[]>([]);
  const [suggestionIndex, setSuggestionIndex] = React.useState<number>(-1);

  let finalData: CandidateData[] = sampleData;
  let finalScoreData: ScoreData[] = [];
  if (data.length > 0) {
    finalData = data;
    finalScoreData = extractScores(finalData);
    console.log('scoreData:', finalScoreData);
    // sort finalData by score
    finalData.sort((a, b) => parseInt(b.score) - parseInt(a.score));
  }

  async function getSuggestion(
    score: string,
    resumeSummary: string,
    jobDescription: string
  ) {
    try {
      const requestData = { score, resumeSummary, jobDescription };
      console.log('Calling generate suggestion API with data:', requestData);
      const response = await axios.post(
        'http://localhost:3001/llm-chat/generate-suggestion',
        requestData
      );
      if (response.status === 200) {
        console.log('Successfully called API!');
        console.log('API response:', response.data.data);
        setSuggestions((prev) => [...prev, response.data.data]);
        console.log('suggestions:', suggestions);
        setSuggestionIndex(suggestionIndex + 1);
      } else {
        alert('Unable to call API.');
      }
      console.log('Suggestion generated');
    } catch (error) {
      console.error('Failed to generate suggestion');
    }
  }

  return (
    <div>
      <h1 className="title">Output Section</h1>
      <ScatterPlot data={finalScoreData} />
      <br />
      <br />
      <div>
        {finalData.map((item, index) => (
          <Accordion key={index} className="accordion">
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              aria-controls={`panel${index}-content`}
              id={`panel${index}-header`}
              className="accordionSummary"
            >
              <Typography>{item.name}</Typography>
              <Typography className="accordionScore">
                {'Score: ' + item.score}
              </Typography>
            </AccordionSummary>
            <AccordionDetails className="accordionDetails">
              <Typography className="accordionSubheader">
                About the score:
              </Typography>
              <Typography className="accordionJustification">
                {item.justification}
              </Typography>
              <Typography className="accordionSubheader">
                Summary of resume:
              </Typography>
              <Typography className="accordionResumeSummary">
                {item.resumeSummary}
              </Typography>
              <br />
              <Button
                variant="contained"
                color="secondary"
                onClick={() =>
                  getSuggestion(item.score, item.resumeSummary, jobDescription)
                }
              >
                Generate suggestion
              </Button>
              {suggestions.length > 0 && (
                <>
                  <Typography className="accordionSubheader">
                    Suggestions for improvement:
                  </Typography>
                  <Typography className="accordionSuggestion">
                    {suggestions[suggestionIndex]}
                  </Typography>
                </>
              )}
            </AccordionDetails>
          </Accordion>
        ))}
      </div>
    </div>
  );
};

export default OutputSection;
