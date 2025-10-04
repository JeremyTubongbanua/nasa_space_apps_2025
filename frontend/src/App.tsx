import './index.css';

function App() {
   return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 gap-2">
         <h1 className="text-2xl font-smeibold">My React App</h1>
         <p>Welcome to my React app!</p>
         <p>This is a simple example of a React application.</p>
         <p>Feel free to explore and modify the code!</p>
         <p className=" text-red-500 text-xl">
            Also please use tailwindcss for styling
         </p>
         <p>Happy coding!</p>
      </div>
   );
}

export default App;
