/**
 * Copyright 2023 Agnostiq Inc.
 *
 * This file is part of Covalent.
 *
 * Licensed under the GNU Affero General Public License 3.0 (the "License").
 * A copy of the License may be obtained with this software package or at
 *
 *      https://www.gnu.org/licenses/agpl-3.0.en.html
 *
 * Use of this file is prohibited except in compliance with the License. Any
 * modifications or derivative works of this file must retain this copyright
 * notice, and modified files must contain a notice indicating that they have
 * been altered from the originals.
 *
 * Covalent is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the License for more details.
 *
 * Relief from the License may be granted by purchasing a commercial license.
 */

import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  Grid,
  Drawer,

} from '@mui/material'
import QElectronTopBar from './QElectronTopBar'
import QElelctronAccordion from './QElelctronAccordion'
import QElectronList from '../qelectron/QElectronList'
import {
  qelectronJobs,
  qelectronJobOverview
} from '../../redux/electronSlice'

const nodeDrawerWidth = 1110

const QElectronDrawer = ({ toggleQelectron, openQelectronDrawer, dispatchId, electronId }) => {
  const dispatch = useDispatch()
  const [expanded, setExpanded] = React.useState(true)
  const [currentJob, setCurrentJob] = React.useState('');
  const [defaultId, setDefaultId] = React.useState('');

  const listData = useSelector(
    (state) => state.electronResults.qelectronJobs
  );

  const overviewData = useSelector(
    (state) => state.electronResults.qelectronJobOverview
  );

  const handleDrawerClose = () => {
    toggleQelectron()
  }

  const rowClickHandler = (job_id) => {
    setCurrentJob(job_id)
    if(job_id!==currentJob) dispatch(qelectronJobOverview({ dispatchId, electronId, jobId: job_id }))
  }

  const details = {
    title: overviewData?.overview?.job_name,
    status: overviewData?.overview?.status,
    id: currentJob
  }

  useEffect(() => {
    setDefaultId('');
    if (!(electronId === null || electronId === undefined) && openQelectronDrawer) {
      const bodyParams = {
        sort_by: 'start_time',
        direction: 'DESC',
        offset: 0
      }
      dispatch(
        qelectronJobs({
          dispatchId,
          electronId,
          bodyParams
        })
      ).then((res) => {
        let job_id = ''
        if (res?.payload && res?.payload.length > 0 && res?.payload[0]?.job_id) job_id = res?.payload[0]?.job_id
        setCurrentJob(job_id)
        setDefaultId(job_id)
        dispatch(qelectronJobOverview({ dispatchId, electronId, jobId: job_id }))
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [openQelectronDrawer])

  // useEffect(() => {
  //   const handleOutsideClick = (event) => {
  //     if (
  //       openQelectronDrawer &&
  //       !event.target.closest('.q-electron-card') &&
  //       !event.target.closest('#nodeDrawer')
  //     ) {
  //       handleDrawerClose()
  //     }
  //   }

  //   document.addEventListener('mousedown', handleOutsideClick)

  //   return () => {
  //     document.removeEventListener('mousedown', handleOutsideClick)
  //   }
  // }, [openQelectronDrawer])

  return (
    <Drawer
      transitionDuration={600}
      id="nodeDrawer"
      sx={(theme) => ({
        position: 'relative',
        width: nodeDrawerWidth,
        '& .MuiDrawer-paper': {
          width: nodeDrawerWidth,
          boxSizing: 'border-box',
          border: 'none',
          p: 3,
          marginRight: '10px',
          marginTop: '22px',
          maxHeight: '95vh',
          bgcolor: (theme) => theme.palette.background.qelectronDrawerbg,
          boxShadow: '0px 16px 50px rgba(0, 0, 0, 0.9)',
          backdropFilter: 'blur(8px)',
          borderRadius: '16px',
          '@media (max-width: 1290px)': {
            height: '92vh',
            marginTop: '70px',
          },
        },
      })}
      anchor="right"
      variant="persistent"
      open={openQelectronDrawer}
      onClose={handleDrawerClose}
      data-testid="nodeDrawer"
    >
      <Grid
        container
        sx={{ position: 'relative', maxHeight: '100%', overflow: 'auto' }}
      >
        <Grid item xs={7.9}>
          <QElectronTopBar
            details={details}
            toggleQelectron={toggleQelectron}
          />
          <QElelctronAccordion expanded={expanded} setExpanded={setExpanded} overviewData={overviewData} />
          <QElectronList expanded={expanded}
            data={listData}
            rowClick={rowClickHandler}
            dispatchId={dispatchId}
            electronId={electronId}
            setExpanded={setExpanded}
            defaultId={defaultId} />
        </Grid>
      </Grid>
    </Drawer>
  )
}

export default QElectronDrawer