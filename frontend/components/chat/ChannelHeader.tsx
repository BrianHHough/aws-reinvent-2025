const CustomChannelHeader = () => {
  const name = "FinStack AI";

  return (
    <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
      <div className="flex items-center gap-2">
        <span className="font-semibold text-lg text-gray-900">{name}</span>
        <span className="flex items-center ml-2">
          <span className="h-2 w-2 bg-green-500 rounded-full inline-block mr-1"></span>
          <span className="text-xs text-green-700 font-medium">online</span>
        </span>
      </div>
    </div>
  );
};

export default CustomChannelHeader;