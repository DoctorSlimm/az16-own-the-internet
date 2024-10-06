import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const MetricItem = ({ label, value }) => (
  <div className="flex flex-col items-center">
    <span className="text-2xl font-bold text-white">{value}</span>
    <span className="text-sm text-gray-200">{label}</span>
  </div>
);

const MetricsDisplay = ({ metrics }) => {
  return (
    <Card className="w-full bg-gray-800 border-gray-700 transition-all duration-300 hover:bg-neon-gradient hover:from-neon-blue hover:via-neon-purple hover:to-neon-pink hover:text-black">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-center text-white">Metrics Overview</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricItem label="Companies Found" value={metrics.companiesFound} />
          <MetricItem label="Issues Checked" value={metrics.issuesChecked} />
          <MetricItem label="Total Followers" value={metrics.totalFollowers} />
          <MetricItem label="Total Issue Responses" value={metrics.totalIssueResponses} />
        </div>
      </CardContent>
    </Card>
  );
};

export default MetricsDisplay;