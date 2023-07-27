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

import _ from 'lodash'
import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  Table,
  TableRow,
  TableHead,
  TableCell,
  TableBody,
  Typography,
  TableContainer,
  TableSortLabel,
  Box,
  styled,
  tableCellClasses,
  tableRowClasses,
  tableBodyClasses,
  tableSortLabelClasses,
  linkClasses,
  Grid,
  SvgIcon,
  Tooltip,
  Skeleton
} from '@mui/material'

import { statusIcon, getLocalStartTime, formatDate, truncateMiddle } from '../../utils/misc'

import { ReactComponent as FilterSvg } from '../../assets/qelectron/filter.svg'
import CopyButton from '../common/CopyButton'
import useMediaQuery from '@mui/material/useMediaQuery'
import {
  qelectronJobs,
} from '../../redux/electronSlice'

const headers = [
  {
    id: 'job_id',
    getter: 'job_id',
    label: 'Job Id / Status',
    sortable: true,
  },
  {
    id: 'start_time',
    getter: 'start_time',
    label: 'Start Time',
    sortable: true,
  },
  {
    id: 'executor',
    getter: 'executor',
    label: 'Executor',
    sortable: true,
  },
]

// const ResultsTableToolbar = ({ query, onSearch, setQuery }) => {
//   return (
//     <Toolbar disableGutters sx={{ mb: 1, width: '260px', height: '32px' }}>
//       <Input
//         fullWidth
//         sx={{
//           px: 1,
//           py: 0.5,
//           height: '32px',
//           border: '1px solid #303067',
//           borderRadius: '60px',
//         }}
//         disableUnderline
//         placeholder="Search in logs"
//         value={query}
//         onChange={(e) => onSearch(e)}
//         startAdornment={
//           <InputAdornment position="start">
//             <SearchIcon sx={{ color: 'text.secondary', fontSize: 16 }} />
//           </InputAdornment>
//         }
//         endAdornment={
//           <InputAdornment
//             position="end"
//             sx={{ visibility: !!query ? 'visible' : 'hidden' }}
//           >
//             <IconButton
//               size="small"
//               onClick={() => setQuery('')}
//               data-testid="clear"
//             >
//               <ClearIcon fontSize="inherit" sx={{ color: 'text.secondary' }} />
//             </IconButton>
//           </InputAdornment>
//         }
//       />
//     </Toolbar>
//   )
// }

const ResultsTableHead = ({ order, orderBy, onSort }) => {
  return (
    <TableHead sx={{ position: 'sticky', zIndex: 19 }}>
      <TableRow>
        {_.map(headers, (header) => {
          return (
            <TableCell
              key={header.id}
              sx={(theme) => ({
                borderColor:
                  theme.palette.background.coveBlack03 + '!important',
              })}
            >
              {header.sortable ? (
                <TableSortLabel
                  data-testid="tableHeader"
                  active={orderBy === header.id}
                  direction={orderBy === header.id ? order : 'asc'}
                  onClick={() => onSort(header.id)}
                  sx={{
                    fontSize: '12px',
                    width: '100%',
                    mr: header.id === 'job_id' ? 20 : null,
                    '.Mui-active': {
                      color: (theme) => theme.palette.text.secondary,
                    },
                  }}
                >
                  {header.id === 'job_id' && (
                    <span style={{ flex: 'none' }}>
                      <SvgIcon
                        aria-label="view"
                        sx={{
                          display: 'flex',
                          justifyContent: 'flex-end',
                          mr: 0,
                          mt: 0.8,
                          pr: 0,
                        }}
                      >
                        <FilterSvg />
                      </SvgIcon>
                    </span>
                  )}
                  {header.label}
                </TableSortLabel>
              ) : (
                header.label
              )}
            </TableCell>
          )
        })}
      </TableRow>
    </TableHead>
  )
}

const StyledTable = styled(Table)(({ theme }) => ({
  // stripe every odd body row except on select and hover
  // [`& .MuiTableBody-root .MuiTableRow-root:nth-of-type(odd):not(.Mui-selected):not(:hover)`]:
  //   {
  //     backgroundColor: theme.palette.background.paper,
  //   },

  // customize text
  [`& .${tableBodyClasses.root} .${tableCellClasses.root}, & .${tableCellClasses.head}`]:
  {
    fontSize: '1rem',
  },

  // subdue header text
  [`& .${tableCellClasses.head}, & .${tableSortLabelClasses.active}`]: {
    color: theme.palette.text.tertiary,
    backgroundColor: 'transparent',
  },

  // copy btn on hover
  [`& .${tableBodyClasses.root} .${tableRowClasses.root}`]: {
    '& .copy-btn': { visibility: 'hidden' },
    '&:hover .copy-btn': { visibility: 'visible' },
  },

  // customize hover
  [`& .${tableBodyClasses.root} .${tableRowClasses.root}:hover`]: {
    backgroundColor: theme.palette.background.coveBlack02,

    [`& .${tableCellClasses.root}`]: {
      borderColor: 'transparent',
      paddingTop: 4,
      paddingBottom: 4,
    },
    [`& .${linkClasses.root}`]: {
      color: theme.palette.text.secondary,
    },
  },

  [`& .${tableBodyClasses.root} .${tableRowClasses.root}`]: {
    backgroundColor: 'transparent',
    cursor: 'pointer',

    [`& .${tableCellClasses.root}`]: {
      borderColor: 'transparent',
      paddingTop: 4,
      paddingBottom: 4,
    },
    // [`& .${linkClasses.root}`]: {
    //   color: theme.palette.text.secondary,
    // },
  },

  // customize selected
  [`& .${tableBodyClasses.root} .${tableRowClasses.root}.Mui-selected`]: {
    backgroundColor: theme.palette.background.coveBlack02,
  },
  [`& .${tableBodyClasses.root} .${tableRowClasses.root}.Mui-selected:hover`]: {
    backgroundColor: theme.palette.background.default,
  },

  // customize border
  [`& .${tableCellClasses.root}`]: {
    borderColor: 'transparent',
    paddingTop: 4,
    paddingBottom: 4,
  },

  [`& .${tableCellClasses.root}:first-of-type`]: {
    borderTopLeftRadius: 8,
    borderBottomLeftRadius: 8,
  },
  [`& .${tableCellClasses.root}:last-of-type`]: {
    borderTopRightRadius: 8,
    borderBottomRightRadius: 8,
  },
}))

const QElectronList = ({ expanded, data, rowClick, electronId, dispatchId, setExpanded, defaultId }) => {
  const dispatch = useDispatch()
  const [selected, setSelected] = useState([])
  const [selectedId, setSelectedId] = useState(defaultId)
  const [sortColumn, setSortColumn] = useState('start_time')
  const [sortOrder, setSortOrder] = useState('DESC')
  const isHeightAbove850px = useMediaQuery('(min-height: 850px)')
  const isHeightAbove940px = useMediaQuery('(min-height: 940px)')
  const isHeightAbove1040px = useMediaQuery('(min-height: 1040px)')
  const isFetching = useSelector(
    (state) => state.electronResults.qelectronJobsList.isFetching
  )

  useEffect(() => {
    setSelectedId(defaultId)
  }, [defaultId])

  useEffect(() => {
    if (electronId) {
      const bodyParams = {
        sort_by: sortColumn,
        direction: sortOrder,
        offset: 0
      }
      dispatch(
        qelectronJobs({
          dispatchId,
          electronId,
          bodyParams
        })
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sortColumn, sortOrder])

  const handleChangeSort = (column) => {
    setSelected([])
    const isAsc = sortColumn === column && sortOrder === 'asc'
    setSortOrder(isAsc ? 'desc' : 'asc')
    setSortColumn(column)
  }

  // const getHeight = () => {
  //   if (xlmatches) {
  //     return expanded ? '23rem' : '40rem'
  //   } else if (xxlmatches) {
  //     return expanded ? '63rem' : '40rem'
  //   } else if (slmatches) {
  //     return expanded ? '24rem' : '48rem'
  //   } else {
  //     return expanded ? '16rem' : '32rem'
  //   }
  // }

  return (
    <Grid
      mt={3}
      px={0}
      sx={{
        height: expanded ? '17rem' : '33rem',
        ...(isHeightAbove850px && {
          height: expanded ? '23.5rem' : '39.25rem',
        }),
        ...(isHeightAbove940px && {
          height: expanded ? '29rem' : '44.75rem',
        }),
        ...(isHeightAbove1040px && {
          height: expanded ? '36rem' : '51.5rem',
        }),
        overflow: 'auto',
        background: (theme) => theme.palette.background.qListBg,
      }}
    >
      <Box data-testid="logsTable">
        {!isFetching && data && (
          <Grid>
            <TableContainer
              sx={{
                borderRadius: _.isEmpty(data) && !data ? '0px' : '8px',
              }}
            >
              <StyledTable stickyHeader>
                {!(_.isEmpty(data)) &&
                  <ResultsTableHead
                    //   totalRecords={totalRecords}
                    order={sortOrder}
                    orderBy={sortColumn}
                    numSelected={_.size(selected)}
                    total={_.size(data)}
                    onSort={handleChangeSort}
                  />}

                <TableBody>
                  {data &&
                    data.map((result, index) => (
                      <>
                        <TableRow
                          sx={{
                            height: '2.5rem'
                          }}
                          data-testid="copyMessage"
                          data-tip
                          data-for="logRow"
                          onClick={() => {
                            setExpanded(true);
                            setSelectedId(result?.job_id)
                            rowClick(result?.job_id)
                          }}
                          hover
                          selected={result?.job_id === selectedId}
                          key={index}
                        >
                          <TableCell
                            sx={{
                              fontFamily: (theme) => theme.typography.logsFont,
                            }}
                          >
                            <Grid
                              sx={{
                                fontSize: '14px',
                                display: 'flex',
                                alignItems: 'center',
                              }}
                            >
                              {statusIcon(result?.status)}
                              <Tooltip title={result?.job_id} placement="left">
                                <Typography
                                  component="span"
                                  sx={{
                                    mx: 1,
                                    verticalAlign: 'middle',
                                    fontSize: '1 rem',
                                    color: (theme) => theme.palette.text.secondary,
                                  }}
                                  width="13rem"
                                >
                                  {truncateMiddle(result?.job_id, 8, 13)}
                                </Typography>
                              </Tooltip>
                              <CopyButton
                                isBorderPresent
                                content={result?.job_id}
                                backgroundColor='#08081A'
                              />
                            </Grid>
                          </TableCell>
                          <TableCell>
                            <Box
                              sx={{
                                display: 'flex',
                                fontSize: '14px',
                              }}
                            >
                              {formatDate(getLocalStartTime(result?.start_time))}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Box
                              sx={{
                                display: 'flex',
                                fontSize: '14px',
                              }}
                            >
                              {result.executor}
                            </Box>
                          </TableCell>
                        </TableRow>
                        {/* <ReactTooltip
                          id="logRow"
                          place="top"
                          effect="float"
                          arrowColor="#1C1C46"
                          backgroundColor="#1C1C46"
                          delayShow={300}
                        >
                          {!copied ? 'Click to copy log message' : 'Copied'}
                        </ReactTooltip> */}
                      </>
                    ))}
                </TableBody>
              </StyledTable>
            </TableContainer>

            {_.isEmpty(data) && !isFetching && (
              <Typography
                sx={{
                  textAlign: 'center',
                  color: 'text.secondary',
                  fontSize: 'h6.fontSize',
                  paddingTop: 9,
                  paddingBottom: 2,
                }}
              >
                No results found.
              </Typography>
            )}
          </Grid>
        )}
      </Box>
      {isFetching && _.isEmpty(data) && (
        <>
          {/*  */}
          {/* <Skeleton variant="rectangular" height={50} /> */}
          <TableContainer>
            <StyledTable>
              <TableBody>
                {[...Array(3)].map(() => (
                  <TableRow key={Math.random()} sx={{
                    height: '2.5rem',
                  }}
                  >
                    <TableCell>
                      <Skeleton sx={{ my: 1, mx: 1 }} />
                    </TableCell>
                    <TableCell>
                      <Skeleton sx={{ my: 1, mx: 1 }} />
                    </TableCell>
                    <TableCell>
                      <Skeleton sx={{ my: 1, mx: 1 }} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </StyledTable>
          </TableContainer>
        </>
      )
      }
    </Grid >
  )
}

export default QElectronList