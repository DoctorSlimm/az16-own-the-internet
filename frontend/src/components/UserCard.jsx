import React, { useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ChevronDown, ChevronUp } from 'lucide-react';

const UserCard = ({ user }) => {
  const [isActivityOpen, setIsActivityOpen] = useState(false);

  return (
    <Card className="bg-gray-800 border-gray-700 transition-all duration-300 hover:bg-neon-gradient hover:from-neon-blue hover:via-neon-purple hover:to-neon-pink hover:text-black relative overflow-hidden">
      <div 
        className="h-1 bg-neon-blue absolute top-0 left-0" 
        style={{ width: `${user.confidence * 100}%` }} 
        title={`Confidence: ${(user.confidence * 100).toFixed(1)}%`}
      />
      <CardContent className="p-4 pt-5">
        <div className="flex items-center space-x-4">
          <Avatar className="h-12 w-12 ring-2 ring-neon-blue">
            <AvatarImage src={user.profileImage} alt={user.displayName} />
            <AvatarFallback className="bg-neon-purple text-white">{user.displayName.charAt(0)}</AvatarFallback>
          </Avatar>
          <div className="flex-grow">
            <h3 className="text-xl font-bold text-white">{user.displayName}</h3>
            <a href={user.githubProfileUrl} target="_blank" rel="noopener noreferrer" className="text-sm text-neon-blue hover:text-neon-pink transition-colors">
              GitHub Profile
            </a>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-white"><strong className="text-neon-blue">Followers:</strong> {user.followerCount}</span>
            <span className="text-white"><strong className="text-neon-blue">Issue Responses:</strong> {user.issueResponseCount}</span>
          </div>
        </div>
        <div className="mt-2 text-white">
          <span><strong className="text-neon-blue">Company:</strong> {user.company || 'N/A'}</span>
          <span className="ml-4"><strong className="text-neon-blue">Location:</strong> {user.location || 'N/A'}</span>
        </div>
        <div className="mt-2 text-white">
          <strong className="text-neon-blue">Labels:</strong> {user.labels.join(', ')}
        </div>
        <div className="mt-2">
          <button
            onClick={() => setIsActivityOpen(!isActivityOpen)}
            className="flex items-center justify-between w-full py-2 px-4 bg-gray-700 hover:bg-gray-600 rounded-md transition-colors text-white"
          >
            <span className="text-neon-blue font-bold">Recent Activity</span>
            {isActivityOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
          {isActivityOpen && (
            <ul className="list-disc list-inside mt-2 text-white">
              {user.timeline.map((activity, index) => (
                <li key={index} className="text-sm mb-1">
                  <a href={activity.url} target="_blank" rel="noopener noreferrer" className="text-neon-blue hover:text-neon-pink">
                    {activity.url}: {activity.url}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default UserCard;