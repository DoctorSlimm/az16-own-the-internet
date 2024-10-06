import axios from 'axios';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import SearchForm from '../components/SearchForm';
import UserCard from '../components/UserCard';
import MetricsDisplay from '../components/MetricsDisplay';



// Example data
import exampleUsers from './example-users.json';
import exampleMetrics from './example-metrics.json';

const fetchDemoUsers = async (query) => {

    // Simulate API call with a delay
    await new Promise(resolve => setTimeout(resolve, 500));
    const sortedUsers = exampleUsers.sort((a, b) => b.confidence - a.confidence);

    // No need to modify the users' data here
    return sortedUsers;
};


// Fetch users from the API (running same container)
const baseURL = "https://main-5868-5395c8d0-2whwroq0.onporter.run"       // API base URL
// const baseURL = "https://nerdy.ngrok.io"       // API base URL

const fetchApiUsers = async (query) => {



  try {

    // Perform API POST request with axios
    const apiClient = axios.create({
        baseURL: baseURL,
        headers: {'x-api-key': 'az16-own-the-internet'}
    });


    // Make the API request
    const response = await apiClient.post('/inference', {query: query});
    console.log('Response:', response);

    // Assuming the response has a data field with the users lol.
    const sortedUsers = response.data.data.sort((a, b) => b.confidence - a.confidence);

    // Return the sorted users
    return sortedUsers;

  } catch (error) {

    console.error('Error fetching users:', error);

    throw error; // Rethrow the error so it can be handled elsewhere

  }
};


const fetchUsers = async (query) => {

  try {

    // check if DEMO in query (use demo data)
    if (query === 'DEMO') {

        return fetchDemoUsers(query);

    } else {

        return fetchApiUsers(query);
    }

  } catch (error) {
    console.error('Error fetching users:', error);
    throw error; // Rethrow the error so it can be handled elsewhere
  }
};


const HexagonLoader = () => (
    <div className="flex justify-center items-center h-32">
        <div className="relative w-16 h-16">
            <div className="absolute inset-0 bg-neon-blue opacity-25 animate-ping" style={{clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)"}}></div>
            <div className="absolute inset-0 bg-neon-blue" style={{clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)"}}></div>
            <div className="absolute inset-2 bg-gray-900" style={{clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)"}}></div>
        </div>
    </div>
);

const Index = () => {
    const [searchQuery, setSearchQuery] = React.useState('');

    const { data: users, isLoading, isError, error, refetch } = useQuery({
        queryKey: ['users', searchQuery],
        queryFn: () => fetchUsers(searchQuery),
        enabled: false,
    });

    const handleSearch = (query) => {
        setSearchQuery(query);
        refetch();
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white p-8">
            <div className="max-w-6xl mx-auto">
                <h1 className="text-5xl font-light mb-8 text-left bg-clip-text text-transparent bg-neon-gradient from-neon-blue via-neon-purple to-neon-pink">360NoScope</h1>
                <p className="text-lg mb-2 text-left">Find developers facing issues you solve. Activate your Squad</p>
                <SearchForm onSearch={handleSearch} />
                {isLoading && <HexagonLoader />}
                {isError && <p className="text-center mt-4 text-red-500">Error: {error.message}</p>}
                {users && (
                    <>
                        <div className="mt-8 mb-8">
                            <MetricsDisplay metrics={exampleMetrics} />
                        </div>
                        <div className="space-y-4 mt-8">
                            {users.map((user) => (
                                <UserCard key={user.id} user={user} />
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default Index;