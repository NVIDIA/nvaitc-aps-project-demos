// SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useState } from 'react';
import './App.css';
import InputSection from './components/InputSection';
import OutputSection from './components/OutputSection';
import Header from './components/Header';
import { CandidateData } from './components/InputSection';

function App() {
  const [candidateData, setCandidateData] = useState<CandidateData[]>([]);
  const [globalJobDescription, setGlobalJobDescription] = useState<string>('');

  useEffect(() => {
    console.log('candidateData updated:', candidateData);
    if (candidateData.length > 0) {
      console.log('candidateData:', candidateData[0]);
      console.log('candidateData.name:', candidateData[0].name);
    }
  }, [candidateData]);

  return (
    <div className="App">
      <Header />
      <div style={{ display: 'flex', width: '100%' }}>
        <div
          style={{
            flex: 1,
            padding: '16px',
            border: 'solid',
            borderRightWidth: '0.5px',
          }}
        >
          <InputSection
            setCandidateData={setCandidateData}
            setGlobalJobDescription={setGlobalJobDescription}
          />
        </div>
        <div
          style={{
            flex: 1,
            padding: '16px',
            border: 'solid',
            borderLeftWidth: '0.5px',
          }}
        >
          <OutputSection
            data={candidateData}
            jobDescription={globalJobDescription}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
