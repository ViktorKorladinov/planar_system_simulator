import {useRouter} from 'next/navigation';
import {TbClock, TbGrid3X3, TbTruck, TbUsers} from 'react-icons/tb';
import {HiBeaker} from 'react-icons/hi';
import Image from 'next/image';
import {formatTimestamp} from '@/utils/timeParser';
import {MdOutlinePrecisionManufacturing} from 'react-icons/md';
import {PiWashingMachineDuotone} from 'react-icons/pi';

const SimulationCard = ({simulationDetail}) => {
  const router = useRouter();
  const topology = simulationDetail.topology_info?.topology || 'unknown';
  const n_tiles = simulationDetail.topology_info?.n_tiles || 0;
  const n_interfaces = simulationDetail.topology_info?.n_interfaces || 0;
  const n_dispensers = simulationDetail.topology_info?.n_dispensers || 0;
  
  const movers = simulationDetail.mover_amount || 0;
  const patients = simulationDetail.order_amount || 0;
  const dose = simulationDetail.dispensing_time || 0; // mapped from dispensing_time or 0

  const metrics = [
    {icon: <HiBeaker/>, label: 'Dose', value: dose},
    {icon: <TbTruck/>, label: 'Movers', value: movers},
    {icon: <TbUsers/>, label: 'Patients', value: patients},
    {icon: <TbGrid3X3/>, label: 'Tiles', value: n_tiles + n_interfaces},
    {
      icon: <MdOutlinePrecisionManufacturing/>,
      label: 'Interfaces',
      value: n_interfaces,
    },
    {
      icon: <PiWashingMachineDuotone/>,
      label: 'Dispensers',
      value: n_dispensers,
    },
  ];

  return (
      <div
          onClick={() => router.push(`/${simulationDetail.id}/simulator`)}
          className="w-[300px] min-h-[350px] rounded-lg overflow-hidden shadow-md transition-shadow duration-200 bg-white hover:shadow-lg cursor-pointer"
      >
        <div className="relative bg-blue-200 p-2 text-gray-800">
          <h2 className="m-0 text-xl font-medium capitalize">{topology} simulation</h2>
        </div>
        <div className="card-content p-4 flex flex-col justify-between h-[90%]">
          {topology === 'custom' ? (
              <img
                  src={`https://api.dicebear.com/9.x/shapes/svg?seed=${simulationDetail.id || 'custom'}&backgroundColor=e2e8f0`}
                  alt="Custom Simulation Image"
                  style={{ position: 'absolute', top: 0, left: 0, bottom: 0, right: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.2, zIndex: 0 }}
              />
          ) : (
              <Image
                  fill={true}
                  src={`layouts/${topology}.svg`}
                  alt="Simulation Image"
                  style={{ objectFit: 'cover', opacity: 0.2, zIndex: 0 }}
              />
          )}
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4 text-sm">
              {metrics.map(({icon, label, value}) => (
                  <div key={label}
                       className="flex flex-col items-center justify-center">
                <span
                    className="w-5 h-5 flex items-center justify-center mb-1 text-gray-700">
                  {icon}
                </span>
                    <span className="font-medium text-gray-800">{value}</span>
                    <span className="text-xs text-gray-500">{label}</span>
                  </div>
              ))}
            </div>

            <div
                className="flex items-center gap-2 text-gray-400 border-t pt-2">
            <span className="w-5 h-5 flex items-center justify-center">
              <TbClock/>
            </span>
              <span>{formatTimestamp(simulationDetail.calculated_at)}</span>
            </div>
          </div>
        </div>
      </div>
  );
};

export default SimulationCard;