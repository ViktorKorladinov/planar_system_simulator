import { NavLink, useLocation, useNavigate } from 'react-router-dom';

export default function TopNav() {
    const location = useLocation();
    const navigate = useNavigate();

    const linkClass = ({ isActive }: { isActive: boolean }) =>
        `px-4 py-4 text-sm font-medium transition-all border-b-2 whitespace-nowrap ${
            isActive
                ? 'border-black-500 text-black-600'
                : 'border-transparent text-gray-500 hover:text-gray-900 hover:border-gray-300'
        }`;

    const createBtnClass = "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:text-gray-900 px-4 py-2 text-sm font-medium rounded-md shadow-sm transition-colors";

    // Helper function to render the correct buttons based on the URL
    const renderActionButtons = () => {
        switch (location.pathname) {
            case '/':
            case '/experiments':
                return (
                    <button
                        className={createBtnClass}
                        onClick={() => navigate('/experiments?create=true')}
                    >
                        Create Experiment
                    </button>
                );
            case '/layouts':
                return (
                    <>
                        <button
                            className={createBtnClass}
                            onClick={() => navigate('/layouts?create=true')}
                        >
                            Create Layout
                        </button>
                        <button
                            className={createBtnClass}
                            onClick={() => navigate('/layouts?create=true&upload=true')}
                        >
                            Load from File
                        </button>
                    </>
                );
            case '/ingredient-lists':
                return (
                    <button
                        className={createBtnClass}
                        onClick={() => navigate('/ingredient-lists?create=true')}
                    >
                        Create Ingredient List
                    </button>
                );
            case '/configurations':
                return (
                    <button
                        className={createBtnClass}
                        onClick={() => navigate('/configurations?create=true')}
                    >
                        Create Configuration
                    </button>
                );
            case '/order-lists':
                return (
                    <button
                        className={createBtnClass}
                        onClick={() => navigate('/order-lists?create=true')}
                    >
                        Create Order List
                    </button>
                );
            case '/batches':
                return (
                    <>
                        <button
                            className={createBtnClass}
                            onClick={() => navigate('/batches?create=true')}
                        >
                            Create Batch
                        </button>
                        <button
                            className={createBtnClass}
                            onClick={() => navigate('/batches?create-fast=true')}
                        >
                            Create Batch Fast
                        </button>
                    </>
                );
            default:
                return null;
        }
    };

    return (
        <nav className="bg-white w-full flex items-center justify-between px-4 sm:px-6 border-b border-gray-200 shadow-sm relative z-10 gap-x-6 flex-wrap md:flex-nowrap">

            {/* Logo */}
            <div className="font-bold text-xl text-gray-900 tracking-tight shrink-0 py-4 order-1">
                Experiment<span className="text-green-700">Configurator</span>
            </div>

            {/* Tabs */}
            <div className="order-3 md:order-2 w-full md:w-auto md:flex-1 flex space-x-1 pt-1 overflow-x-auto min-w-0 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                <NavLink to="/" className={linkClass}>Experiments</NavLink>
                <NavLink to="/configurations" className={linkClass}>Configurations</NavLink>
                <NavLink to="/layouts" className={linkClass}>Layouts</NavLink>
                <NavLink to="/ingredient-lists" className={linkClass}>Ingredient Lists</NavLink>
                <NavLink to="/order-lists" className={linkClass}>Order Lists</NavLink>
                <NavLink to="/batches" className={linkClass}>Batches</NavLink>
            </div>

            {/* Buttons */}
            <div className="order-2 md:order-3 flex items-center space-x-2 sm:space-x-3 shrink-0 py-3">
                {renderActionButtons()}
            </div>

        </nav>
    );
}