import React from "react";
import { ClipLoader } from "react-spinners";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import remarkGfm from "remark-gfm";

// Convert to forwardRef to accept refs from parent components
const Message = React.forwardRef(({ text, isUser, isLoading }, ref) => {
  // if the message is loading, display a loading spinner
  if (isLoading) {
    return (
      <div
        ref={ref}
        className={`flex items-center my-2 w-fit ${
          isUser ? "self-end ml-12 flex-row-reverse" : "mr-12"
        }`}
      >
        <div
          className={`flex items-center p-3 rounded-xl bg-gradient-to-tr ${
            isUser
              ? "from-blue-100 to-cyan-100 dark:from-blue-900 dark:to-cyan-900"
              : "from-neutral-100 to-slate-100 dark:from-neutral-800 dark:to-neutral-800"
          }`}
        >
          <ClipLoader size={15} color="rgb(115 115 115)" />
          <div className="ml-1 text-neutral-500 dark:text-neutral-400">
            Thinking...
          </div>
        </div>
      </div>
    );
  }

  // if the message is not loading, display the message text with markdown
  return (
    <div
      ref={ref}
      className={`flex p-2 ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`p-3 rounded-xl bg-gradient-to-tr max-w-prose w-fit ${
          isUser
            ? "from-blue-100 to-cyan-100 dark:from-slate-700 dark:to-slate-700 dark:text-neutral-100"
            : "from-neutral-100 to-neutral-100 dark:from-neutral-800 dark:to-neutral-800 dark:text-neutral-200"
        }`}
      >
        <div className="markdown-content">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({node, inline, className, children, ...props}) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={atomDark}
                    language={match[1]}
                    PreTag="div"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={`${className} bg-gray-200 dark:bg-gray-700 px-1 rounded`} {...props}>
                    {children}
                  </code>
                );
              },
              // Style for links
              a: ({node, ...props}) => (
                <a 
                  className="text-blue-500 hover:underline" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  {...props} 
                />
              ),
              // Style for paragraphs
              p: ({node, ...props}) => (
                <p className="mb-4 last:mb-0" {...props} />
              ),
              // Style for headings
              h1: ({node, ...props}) => (
                <h1 className="text-2xl font-bold mb-4 mt-2" {...props} />
              ),
              h2: ({node, ...props}) => (
                <h2 className="text-xl font-bold mb-3 mt-2" {...props} />
              ),
              h3: ({node, ...props}) => (
                <h3 className="text-lg font-bold mb-2 mt-2" {...props} />
              ),
              // Style for lists
              ul: ({node, ...props}) => (
                <ul className="list-disc pl-6 mb-4" {...props} />
              ),
              ol: ({node, ...props}) => (
                <ol className="list-decimal pl-6 mb-4" {...props} />
              ),
              // Style for blockquotes
              blockquote: ({node, ...props}) => (
                <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 my-4 italic" {...props} />
              ),
              // Style for tables
              table: ({node, ...props}) => (
                <div className="overflow-x-auto mb-4">
                  <table className="min-w-full divide-y divide-gray-300 dark:divide-gray-600" {...props} />
                </div>
              ),
              thead: ({node, ...props}) => (
                <thead className="bg-gray-100 dark:bg-gray-800" {...props} />
              ),
              tbody: ({node, ...props}) => (
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700" {...props} />
              ),
              tr: ({node, ...props}) => (
                <tr className="hover:bg-gray-50 dark:hover:bg-gray-900" {...props} />
              ),
              th: ({node, ...props}) => (
                <th className="px-3 py-2 text-left text-sm font-medium text-gray-700 dark:text-gray-300" {...props} />
              ),
              td: ({node, ...props}) => (
                <td className="px-3 py-2 text-sm" {...props} />
              ),
            }}
          >
            {text}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
});

// Add display name for React DevTools
Message.displayName = "Message";

export default Message;
