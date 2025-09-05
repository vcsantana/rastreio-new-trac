import { Divider, List } from '@mui/material';
import StarIcon from '@mui/icons-material/Star';
import TimelineIcon from '@mui/icons-material/Timeline';
import PauseCircleFilledIcon from '@mui/icons-material/PauseCircleFilled';
import PlayCircleFilledIcon from '@mui/icons-material/PlayCircleFilled';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import FormatListBulletedIcon from '@mui/icons-material/FormatListBulleted';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import BarChartIcon from '@mui/icons-material/BarChart';
import RouteIcon from '@mui/icons-material/Route';
import EventRepeatIcon from '@mui/icons-material/EventRepeat';
import NotesIcon from '@mui/icons-material/Notes';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import { useLocation } from 'react-router-dom';
import { useTranslation } from '../../common/components/LocalizationProvider';
import { useAdministrator, useRestriction } from '../../common/util/permissions';
import MenuItem from '../../common/components/MenuItem';

const ReportsMenu = () => {
  const t = useTranslation();
  const location = useLocation();

  const admin = useAdministrator();
  const readonly = useRestriction('readonly');

  return (
    <>
      <List>
        <MenuItem
          title={t('reportCombined')}
          link="/reports/combined"
          icon={<StarIcon />}
          selected={location.pathname === '/reports/combined'}
        />
        <MenuItem
          title={t('reportEvents')}
          link="/reports/events"
          icon={<NotificationsActiveIcon />}
          selected={location.pathname === '/reports/events'}
        />
        <MenuItem
          title={t('reportTrips')}
          link="/reports/trips"
          icon={<PlayCircleFilledIcon />}
          selected={location.pathname === '/reports/trips'}
        />
        <MenuItem
          title={t('reportStops')}
          link="/reports/stops"
          icon={<PauseCircleFilledIcon />}
          selected={location.pathname === '/reports/stops'}
        />
        <MenuItem
          title={t('reportSummary')}
          link="/reports/summary"
          icon={<FormatListBulletedIcon />}
          selected={location.pathname === '/reports/summary'}
        />
        <MenuItem
          title={t('reportChart')}
          link="/reports/chart"
          icon={<TrendingUpIcon />}
          selected={location.pathname === '/reports/chart'}
        />
        <MenuItem
          title={t('reportReplay')}
          link="/replay"
          icon={<RouteIcon />}
        />
        <MenuItem
          title={t('reportPositions')}
          link="/reports/route"
          icon={<TimelineIcon />}
          selected={location.pathname === '/reports/route'}
        />
      </List>
      <Divider />
      <List>
        <MenuItem
          title={t('sharedLogs')}
          link="/reports/logs"
          icon={<NotesIcon />}
          selected={location.pathname === '/reports/logs'}
        />
        {!readonly && (
          <MenuItem
            title={t('reportScheduled')}
            link="/reports/scheduled"
            icon={<EventRepeatIcon />}
            selected={location.pathname === '/reports/scheduled'}
          />
        )}
        {admin && (
          <MenuItem
            title={t('statisticsTitle')}
            link="/reports/statistics"
            icon={<BarChartIcon />}
            selected={location.pathname === '/reports/statistics'}
          />
        )}
        {admin && (
          <MenuItem
            title={t('reportAudit')}
            link="/reports/audit"
            icon={<VerifiedUserIcon />}
            selected={location.pathname === '/reports/audit'}
          />
        )}
      </List>
    </>
  );
};

export default ReportsMenu;
