import React from 'react';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const SearchForm = ({ onSearch }) => {
  const [query, setQuery] = React.useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <form onSubmit={handleSubmit} className="flex space-x-2">
      <Input
        type="text"
        placeholder="xApiKey:product_description"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="flex-grow bg-gray-800 border-gray-700 text-white placeholder-gray-400 focus:ring-neon-blue focus:border-neon-blue"
      />
      <Button type="submit" className="bg-neon-gradient from-neon-blue to-neon-purple text-white hover:from-neon-purple hover:to-neon-pink transition-all duration-300">
        Let's Own the Internet
      </Button>
    </form>
  );
};

export default SearchForm;