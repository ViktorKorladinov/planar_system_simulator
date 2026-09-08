import {useEffect, useState} from 'react';

interface ToastNotificationProps {
    message: string;
    type: 'success' | 'error';
    actionText?: string;
    onActionClick?: () => void;
}

export default function ToastNotification({message, type, actionText, onActionClick}: ToastNotificationProps) {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        const animationFrame = requestAnimationFrame(() => setIsVisible(true));
        return () => cancelAnimationFrame(animationFrame);
    }, []);

    return (
        <div
            onClick={onActionClick}
            className={`pointer-events-auto w-max px-4 py-3 rounded-md shadow-lg text-white font-medium flex items-center space-x-3
                /* Animation Classes */
                transform transition-all duration-300 ease-out
                ${isVisible ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-8 scale-95'}
                
                /* Base Styles */
                ${type === 'success' ? 'bg-green-800' : 'bg-red-800'} 
                ${onActionClick ? 'cursor-pointer hover:shadow-xl hover:-translate-y-1' : ''}`
            }
        >
            <span>{message}</span>
            {actionText && onActionClick && (
                <span className="text-sm underline opacity-80 pl-3 border-l border-white/30">
                    {actionText}
                </span>
            )}
        </div>
    );
}