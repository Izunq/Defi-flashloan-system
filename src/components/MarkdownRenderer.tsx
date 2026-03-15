import React from 'react';
import ReactMarkdown from 'react-markdown';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  return (
    <div className={`prose prose-invert max-w-none ${className}`}>
      <ReactMarkdown
        components={{
          h1: ({ node, ...props }) => <h1 className="text-xl font-bold mt-4 mb-3 text-white" {...props} />,
          h2: ({ node, ...props }) => <h2 className="text-lg font-bold mt-6 mb-3 text-blue-300" {...props} />,
          h3: ({ node, ...props }) => <h3 className="text-md font-bold mt-4 mb-2 text-purple-300" {...props} />,
          p: ({ node, ...props }) => <p className="mb-4 text-gray-200 leading-relaxed" {...props} />,
          ul: ({ node, ...props }) => <ul className="list-disc pl-5 mb-4 space-y-1" {...props} />,
          ol: ({ node, ...props }) => <ol className="list-decimal pl-5 mb-4 space-y-1" {...props} />,
          li: ({ node, ...props }) => <li className="text-gray-300" {...props} />,
          a: ({ node, ...props }) => <a className="text-blue-400 hover:underline" {...props} />,
          code: ({ node, ...props }: any) => {
            const isInlineCode = !props.className?.includes('language-');
            return isInlineCode
              ? <code className="bg-gray-700 px-1 py-0.5 rounded text-gray-200" {...props} />
              : <code className="block bg-gray-700/50 p-3 rounded-md text-gray-200 overflow-x-auto my-4" {...props} />;
          },
          strong: ({ node, ...props }) => <strong className="font-bold text-white" {...props} />,
          em: ({ node, ...props }) => <em className="italic text-gray-300" {...props} />,
          blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-400 my-4" {...props} />,
          hr: ({ node, ...props }) => <hr className="border-gray-700 my-6" {...props} />
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
