// SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export interface ScoreData {
  name: string;
  score: number;
}

const sampleData: ScoreData[] = [];
// const sampleData: ScoreData[] = [
//   { name: 'Alice', score: 8 },
//   { name: 'Bob', score: 6 },
//   { name: 'Charlie', score: 6 },
//   { name: 'Diana', score: 5 },
// ];

interface ScatterPlotProps {
  data: ScoreData[];
}

const ScatterPlot: React.FC<ScatterPlotProps> = ({ data }) => {
  let finalData = sampleData;
  if (data.length > 0) {
    finalData = data;
  }

  return (
    <ResponsiveContainer width="90%" height={300}>
      <ScatterChart>
        <CartesianGrid />
        <XAxis
          type="category"
          dataKey="name" // Use candidate names as the x-axis
          name="Candidate"
          allowDuplicatedCategory={false} // Ensure no duplicate categories
        />
        <YAxis
          type="number"
          dataKey="score" // Use scores as the y-axis
          name="Score"
          domain={[0, 10]} // Scores range from 0 to 10
        />
        <Tooltip cursor={{ strokeDasharray: '3 3' }} />
        <Legend />
        <Scatter name="Candidate Scores" data={finalData} fill="#D4F841" />
      </ScatterChart>
    </ResponsiveContainer>
  );
};

export default ScatterPlot;
