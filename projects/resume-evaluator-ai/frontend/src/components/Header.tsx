// SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import './Header.css'; // Assuming you will add some CSS for styling

const Header: React.FC = () => {
  return (
    <div className="header">
      <h1 className="headline">Resume Evaluator Tool</h1>
      <div className="columns">
        <div className="sub-section">
          <h2 className="sub-headline">Inputs</h2>
          <p className="text">{'1. Candidate resumes (in PDF format)'}</p>
          <p className="text">
            {'2. Company name, Role name and Job description'}
          </p>
        </div>
        <div className="sub-section">
          <h2 className="sub-headline">Outputs</h2>
          <p className="text">{'1. Candidate scores summary'}</p>
          <p className="text">{'2. Candidate suitability explanations'}</p>
          <p className="text">{'3. Candidate resume summaries'}</p>
        </div>
      </div>
    </div>
  );
};

export default Header;
